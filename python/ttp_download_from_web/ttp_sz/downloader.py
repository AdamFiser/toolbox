"""Stahování souborů přes Playwright kontext s retry a bezpečnou extrakcí ZIP.

Stažená data se nezapisují přímo, ale předávají do :mod:`ttp_sz.sync`, který
rozhodne, zda jde o reálnou změnu (kvůli distribuci do tabletů).
"""

from __future__ import annotations

import io
import logging
import os
import time
import zipfile
from pathlib import Path

from .config import Settings
from .filters import should_skip
from .naming import choose_best_filename, infer_ext_from_headers, parse_cd_filename, sanitize
from .sync import Action, Outcome, sync_file

logger = logging.getLogger(__name__)


def _get_with_retry(context, url: str, settings: Settings):
    """Provede GET s několika pokusy a exponenciálním backoffem."""
    last_exc: Exception | None = None
    for attempt in range(1, settings.retries + 1):
        try:
            r = context.request.get(url, timeout=settings.request_timeout_ms)
            if r.ok:
                return r
            logger.warning("⚠ HTTP %s (pokus %s/%s): %s", r.status, attempt, settings.retries, url)
        except Exception as e:  # síťová chyba / timeout
            last_exc = e
            logger.warning("⚠ chyba GET (pokus %s/%s): %s", attempt, settings.retries, e)
        if attempt < settings.retries:
            time.sleep(min(2 ** attempt * 0.5, 10))
    if last_exc is not None:
        logger.error("✗ GET selhal po %s pokusech: %s (%s)", settings.retries, url, last_exc)
    return None


def _resolve_filename(headers: dict, suggested_name: str) -> str:
    """Určí finální název souboru z hlaviček a textu odkazu."""
    cd_name = parse_cd_filename(
        headers.get("content-disposition") or headers.get("Content-Disposition")
    )
    base_name = sanitize(choose_best_filename(cd_name, suggested_name))
    if not os.path.splitext(base_name)[1]:
        base_name += infer_ext_from_headers(headers, base_name) or ""
    return base_name


def _is_within(base: Path, target: Path) -> bool:
    """True, pokud ``target`` leží uvnitř ``base`` (ochrana proti zip-slip)."""
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _extract_zip(body: bytes, target_dir: Path) -> list[Outcome]:
    """Bezpečně rozbalí ZIP přes sync (každý člen jen pokud se reálně mění)."""
    outcomes: list[Outcome] = []
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            dest = (target_dir / info.filename)
            if not _is_within(target_dir, dest):
                logger.warning("⚠ přeskočen člen mimo cílovou složku (zip-slip): %s", info.filename)
                continue
            data = zf.read(info)
            outcomes.append(sync_file(dest.parent, dest.name, data))
    return outcomes


def download_file(context, url: str, suggested_name: str, target_dir: Path, settings: Settings) -> list[Outcome]:
    """Stáhne soubor, vyfiltruje nechtěné a uloží/rozbalí přes sync.

    Vrací seznam :class:`Outcome` (u ZIP jeden na každý rozbalený soubor).
    """
    target_dir = Path(target_dir)
    logger.info("→ GET %s", url)

    r = _get_with_retry(context, url, settings)
    if r is None:
        return []

    headers, body = r.headers, r.body()
    base_name = _resolve_filename(headers, suggested_name)

    if should_skip(base_name):
        logger.info("⏭ přeskočeno (filtr): %s", base_name)
        return []

    if base_name.lower().endswith(".zip"):
        try:
            return _extract_zip(body, target_dir)
        except zipfile.BadZipFile:
            logger.warning("⚠ soubor má .zip, ale nejde rozbalit: %s", base_name)
            return []

    return [sync_file(target_dir, base_name, body)]
