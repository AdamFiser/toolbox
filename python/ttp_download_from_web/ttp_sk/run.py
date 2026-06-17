"""Orchestrace stahování ŽSR: rozbor stránky, výběr verzí, paralelní sync.

Sdílí idempotentní zápisovou vrstvu s SŽ (:func:`ttp_common.sync.sync_file`):
soubory ŽSR mají stabilní název podle identity (např. ``TTP 101 A.pdf``), takže
se zapíše jen reálná změna obsahu (kvůli distribuci do tabletů).
"""

from __future__ import annotations

import logging
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from ttp_common.sync import Action, Outcome, sync_file

from .config import SkSettings
from .fetch import discover
from .versioning import select_latest

logger = logging.getLogger(__name__)

_USER_AGENT = "Mozilla/5.0 (compatible; ttp-downloader/1.0)"


def _get_with_retry(session: requests.Session, url: str, settings: SkSettings):
    """GET s několika pokusy a exponenciálním backoffem."""
    timeout = settings.request_timeout_ms / 1000.0
    for attempt in range(1, settings.retries + 1):
        try:
            r = session.get(url, timeout=timeout)
            if r.ok:
                return r
            logger.warning("⚠ HTTP %s (pokus %s/%s): %s", r.status_code, attempt, settings.retries, url)
        except requests.RequestException as e:
            logger.warning("⚠ chyba GET (pokus %s/%s): %s", attempt, settings.retries, e)
        if attempt < settings.retries:
            time.sleep(min(2 ** attempt * 0.5, 10))
    logger.error("✗ GET selhal: %s", url)
    return None


def _download_one(session, url: str, filename: str, target_dir: Path, settings: SkSettings) -> Outcome | None:
    """Stáhne jeden soubor a idempotentně uloží přes sdílený sync."""
    if filename.lower().endswith(".xml"):
        return None
    logger.info("→ %s", filename)
    r = _get_with_retry(session, url, settings)
    if r is None:
        return None
    return sync_file(target_dir, filename, r.content)


def _ensure_target_writable(settings: SkSettings) -> None:
    try:
        settings.target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(
            f"Cílová složka není dostupná pro zápis: {settings.target_dir} ({e})"
        ) from e


def _log_summary(outcomes: list[Outcome]) -> None:
    counts = Counter(o.action for o in outcomes)
    logger.info("── Přehled změn ──")
    logger.info("   přidáno:    %s", counts.get(Action.WRITE, 0))
    logger.info("   nahrazeno:  %s", counts.get(Action.REPLACE, 0))
    logger.info("   beze změny: %s", counts.get(Action.SKIP, 0))
    for o in outcomes:
        if o.action in (Action.WRITE, Action.REPLACE):
            logger.info("   %s %s", "+" if o.action is Action.WRITE else "~", o.path)


def run(settings: SkSettings) -> list[Outcome]:
    """Spustí celý proces stahování a synchronizace ŽSR."""
    logger.info("Start skriptu (ŽSR)")
    _ensure_target_writable(settings)

    logger.info("Načítám stránku: %s", settings.page_url)
    table_pairs, general = discover(settings)

    # Pro každou identitu vyber nejvyšší číslo změny (zachovej URL).
    by_identity: dict[str, tuple] = {}
    for tbl, url in table_pairs:
        cur = by_identity.get(tbl.identity)
        if cur is None or tbl.change > cur[0].change:
            by_identity[tbl.identity] = (tbl, url)
    latest = list(by_identity.values())
    logger.info(
        "🌲 Tabulek: %s (z %s odkazů), obecných souborů: %s",
        len(latest), len(table_pairs), len(general),
    )

    jobs: list[tuple[str, str]] = [(tbl.filename, url) for tbl, url in latest]
    jobs += [(name, url) for name, url in general]

    session = requests.Session()
    session.headers["User-Agent"] = _USER_AGENT
    target_dir = settings.target_dir

    outcomes: list[Outcome] = []
    with ThreadPoolExecutor(max_workers=settings.workers) as executor:
        logger.info("Stahuji (paralelních stahování: %s)…", settings.workers)
        futures = [
            executor.submit(_download_one, session, url, fname, target_dir, settings)
            for fname, url in jobs
        ]
        for f in as_completed(futures):
            try:
                out = f.result()
                if out is not None:
                    outcomes.append(out)
            except Exception as e:
                logger.error("✗ stahování selhalo: %s", e)

    _log_summary(outcomes)
    logger.info("✅ Hotovo. Cíl: %s", target_dir)
    return outcomes
