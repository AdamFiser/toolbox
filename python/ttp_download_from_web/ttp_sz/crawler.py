"""Orchestrace celého běhu: přihlášení, procházení menu a paralelní stahování.

Procházení menu (Playwright, jednovláknově) běží v hlavním vlákně a objevené
soubory průběžně předává do fondu vláken, který je stahuje **souběžně** s dalším
procházením. Tím se procházení a stahování neblokují navzájem.

Řídí životní cyklus dočasného stavu přihlášení (smaž → přihlas → po dokončení
smaž) a na konci vypíše přehled reálných změn (co se poslalo do tabletů).
"""

from __future__ import annotations

import logging
import os
from collections import Counter, deque
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path

from playwright.sync_api import sync_playwright

from .auth import save_auth
from .config import Settings
from .downloader import DirLocks, build_session, download_file
from .filters import is_excluded_menu_item, should_skip
from .menu import build_target_dir, find_show_links_with_names, read_leftmenu_ttp_tree
from ttp_common.naming import sanitize
from ttp_common.sync import Action, Outcome

logger = logging.getLogger(__name__)


def _menu_items(page) -> list[dict]:
    """Načte položky menu po odfiltrování vyřazených větví (XML)."""
    return [
        it
        for it in (read_leftmenu_ttp_tree(page) or [])
        if not is_excluded_menu_item(it.get("label"), it.get("path"))
    ]


def crawl_and_download(page, session, executor, settings: Settings, dir_locks: DirLocks) -> list[Future]:
    """Projde strom menu (BFS) a průběžně zadává stahování souborů do fondu vláken.

    Vrací seznam :class:`Future` zadaných stahování — volající na ně počká.
    """
    logger.info("Načítám TTP kořen: %s", settings.base_ttp_url)
    page.goto(settings.base_ttp_url, wait_until="networkidle")
    page.wait_for_selector("#leftnav .leftmenu", timeout=15000)

    items = _menu_items(page)
    logger.info("🌲 Načteno %s položek z menu (po filtraci XML).", len(items))

    collected = {it["url"]: it for it in items}
    to_visit = deque(collected.keys())
    visited: set[str] = set()
    seen_files: set[str] = set()
    futures: list[Future] = []

    while to_visit:
        url = to_visit.popleft()
        if url in visited:
            continue
        visited.add(url)

        logger.info("🔎 Procházím %s (%s/%s)…", url, len(visited), len(collected))
        page.goto(url, wait_until="networkidle")
        try:
            page.wait_for_selector("#leftnav .leftmenu", timeout=10000)
        except Exception:
            logger.warning("⚠ levé menu nenačteno (pokračuji)")

        # Objev další větve menu.
        for it in _menu_items(page):
            if it["url"] not in collected:
                collected[it["url"]] = it
                to_visit.append(it["url"])

        # Zadej ke stažení soubory z této stránky (běží souběžně s dalším procházením).
        item = collected[url]
        target_dir = Path(build_target_dir(settings.target_dir, item.get("path"), item.get("label")))
        target_dir.mkdir(parents=True, exist_ok=True)

        show_links = find_show_links_with_names(page, url)
        queued = 0
        for link in show_links:
            durl = link["url"]
            if durl in seen_files:
                continue
            seen_files.add(durl)

            suggested = sanitize(link["name"] or "soubor")
            if should_skip(suggested):
                logger.info("    ⏭ přeskočeno (filtr): %s", suggested)
                continue

            lock = dir_locks.get(target_dir)
            futures.append(
                executor.submit(download_file, session, durl, suggested, target_dir, settings, lock)
            )
            queued += 1

        if queued:
            logger.info("  📑 zadáno ke stažení: %s (souborů na stránce: %s)", queued, len(show_links))

    logger.info("📦 Zadáno celkem %s stahování, čekám na dokončení…", len(futures))
    return futures


def _collect_outcomes(futures: list[Future]) -> list[Outcome]:
    """Posbírá výsledky stahování; chyby jednotlivých úloh nezhroutí celý běh."""
    outcomes: list[Outcome] = []
    for f in as_completed(futures):
        try:
            outcomes.extend(f.result())
        except Exception as e:
            logger.error("✗ stahování selhalo: %s", e)
    return outcomes


def _log_summary(outcomes: list[Outcome]) -> None:
    """Vypíše přehled reálných změn (kolik přidáno/nahrazeno/přeskočeno)."""
    counts = Counter(o.action for o in outcomes)
    added = counts.get(Action.WRITE, 0)
    replaced = counts.get(Action.REPLACE, 0)
    skipped = counts.get(Action.SKIP, 0)
    removed = sum(len(o.removed) for o in outcomes)

    logger.info("── Přehled změn ──")
    logger.info("   přidáno:    %s", added)
    logger.info("   nahrazeno:  %s", replaced)
    logger.info("   smazáno:    %s (staré verze)", removed)
    logger.info("   beze změny: %s", skipped)

    for o in outcomes:
        if o.action in (Action.WRITE, Action.REPLACE):
            logger.info("   %s %s", "+" if o.action is Action.WRITE else "~", o.path)


def _ensure_target_writable(settings: Settings) -> None:
    """Ověří, že cílová (síťová) složka je dostupná pro zápis."""
    try:
        settings.target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(
            f"Cílová složka není dostupná pro zápis: {settings.target_dir} ({e})"
        ) from e


def run(settings: Settings) -> list[Outcome]:
    """Spustí celý proces stahování a synchronizace."""
    logger.info("Start skriptu")
    settings.require_credentials()
    _ensure_target_writable(settings)

    # Dočasný stav přihlášení — vždy čerstvý, po dokončení smazat.
    settings.auth_state_file.unlink(missing_ok=True)
    try:
        logger.info("🔐 Přihlašuji se…")
        save_auth(settings)
        session = build_session(settings.auth_state_file)
        dir_locks = DirLocks()

        with ThreadPoolExecutor(max_workers=settings.download_workers) as executor:
            logger.info("Spouštím prohlížeč (paralelních stahování: %s)…", settings.download_workers)
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=settings.headless)
                context = browser.new_context(storage_state=str(settings.auth_state_file))
                page = context.new_page()

                futures = crawl_and_download(page, session, executor, settings, dir_locks)

                browser.close()

            outcomes = _collect_outcomes(futures)

        _log_summary(outcomes)
        logger.info("✅ Hotovo. Cíl: %s", settings.target_dir)
        return outcomes
    finally:
        settings.auth_state_file.unlink(missing_ok=True)
        logger.info("🧹 Dočasný stav přihlášení odstraněn.")
