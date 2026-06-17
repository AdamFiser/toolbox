"""Orchestrace celého běhu: přihlášení, projití menu, stažení a sync.

Řídí životní cyklus dočasného stavu přihlášení (smaž → přihlas → po dokončení
smaž) a na konci vypíše přehled reálných změn (co se poslalo do tabletů).
"""

from __future__ import annotations

import logging
import os
from collections import Counter, deque
from pathlib import Path

from playwright.sync_api import sync_playwright

from .auth import save_auth
from .config import Settings
from .downloader import download_file
from .filters import is_excluded_menu_item, should_skip
from .menu import build_target_dir, find_show_links_with_names, read_leftmenu_ttp_tree
from .naming import sanitize
from .sync import Action, Outcome

logger = logging.getLogger(__name__)


def _menu_items(page) -> list[dict]:
    """Načte položky menu po odfiltrování vyřazených větví (XML)."""
    return [
        it
        for it in (read_leftmenu_ttp_tree(page) or [])
        if not is_excluded_menu_item(it.get("label"), it.get("path"))
    ]


def crawl_menu(page, settings: Settings) -> list[dict]:
    """Projde strom menu do šířky (BFS) a vrátí všechny nalezené položky."""
    logger.info("Načítám TTP kořen: %s", settings.base_ttp_url)
    page.goto(settings.base_ttp_url, wait_until="networkidle")
    page.wait_for_selector("#leftnav .leftmenu", timeout=15000)

    items = _menu_items(page)
    logger.info("🌲 Načteno %s položek z menu (po filtraci XML).", len(items))

    collected = {it["url"]: it for it in items}
    to_visit = deque(collected.keys())
    visited: set[str] = set()

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

        for it in _menu_items(page):
            if it["url"] not in collected:
                collected[it["url"]] = it
                to_visit.append(it["url"])

    logger.info("📦 Celkem TTP položek ke stažení: %s", len(collected))
    return list(collected.values())


def download_all(page, context, items: list[dict], settings: Settings) -> list[Outcome]:
    """Pro každou položku menu stáhne nalezené soubory a vrátí výsledky syncu."""
    outcomes: list[Outcome] = []
    for i, it in enumerate(items, start=1):
        target_dir = Path(build_target_dir(settings.target_dir, it.get("path"), it.get("label")))
        target_dir.mkdir(parents=True, exist_ok=True)

        rel = os.path.relpath(target_dir, settings.target_dir)
        logger.info("📁 (%s/%s) %s", i, len(items), rel)
        page.goto(it["url"], wait_until="networkidle")

        show_links = find_show_links_with_names(page, it["url"])
        logger.info("  📑 nalezeno Show.aspx odkazů: %s", len(show_links))

        for idx, link in enumerate(show_links, start=1):
            suggested = sanitize(link["name"] or "soubor")
            if should_skip(suggested):
                logger.info("    (%s/%s) ⏭ přeskočeno (filtr): %s", idx, len(show_links), suggested)
                continue
            logger.info("    (%s/%s) ⬇ %s", idx, len(show_links), suggested)
            outcomes.extend(download_file(context, link["url"], suggested, target_dir, settings))
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

        with sync_playwright() as p:
            logger.info("Spouštím prohlížeč…")
            browser = p.chromium.launch(headless=settings.headless)
            context = browser.new_context(storage_state=str(settings.auth_state_file))
            page = context.new_page()

            items = crawl_menu(page, settings)
            outcomes = download_all(page, context, items, settings)

            browser.close()

        _log_summary(outcomes)
        logger.info("✅ Hotovo. Cíl: %s", settings.target_dir)
        return outcomes
    finally:
        settings.auth_state_file.unlink(missing_ok=True)
        logger.info("🧹 Dočasný stav přihlášení odstraněn.")
