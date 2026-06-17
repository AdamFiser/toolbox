"""Stahování souborů přes ``requests`` s retry a bezpečnou extrakcí ZIP.

Stahování je oddělené od Playwrightu (který běží jednovláknově a obstarává
procházení menu): přihlašovací cookies se z Playwright stavu relace přenesou do
``requests.Session``, takže soubory lze stahovat **paralelně** ve více vláknech
souběžně s procházením.

Stažená data se nezapisují přímo, ale předávají do :mod:`ttp_sz.sync`, který
rozhodne, zda jde o reálnou změnu (kvůli distribuci do tabletů).
"""

from __future__ import annotations

import io
import json
import logging
import os
import threading
import time
import zipfile
from pathlib import Path

import requests

from .config import Settings
from .filters import should_skip
from ttp_common.naming import choose_best_filename, infer_ext_from_headers, parse_cd_filename, sanitize
from ttp_common.sync import Action, Outcome, sync_file

logger = logging.getLogger(__name__)

_USER_AGENT = "Mozilla/5.0 (compatible; ttp-downloader/1.0)"


class DirLocks:
    """Poskytuje zámek pro každou cílovou složku (serializace zápisů do ní).

    Sync maže staré verze a čte výpis složky — paralelní zápisy do téže složky
    by se mohly prát, proto se v rámci jedné složky zápis serializuje.
    """

    def __init__(self) -> None:
        self._main = threading.Lock()
        self._locks: dict[str, threading.Lock] = {}

    def get(self, key: Path | str) -> threading.Lock:
        k = str(key)
        with self._main:
            return self._locks.setdefault(k, threading.Lock())


def build_session(storage_state_file: Path) -> requests.Session:
    """Vytvoří ``requests.Session`` s cookies z Playwright stavu relace."""
    session = requests.Session()
    session.headers["User-Agent"] = _USER_AGENT

    data = json.loads(Path(storage_state_file).read_text(encoding="utf-8"))
    for c in data.get("cookies", []):
        try:
            session.cookies.set(
                c["name"], c["value"], domain=c.get("domain"), path=c.get("path", "/")
            )
        except Exception as e:  # poškozený cookie záznam přeskočíme
            logger.warning("⚠ nelze načíst cookie %s: %s", c.get("name"), e)
    return session


def _get_with_retry(session: requests.Session, url: str, settings: Settings):
    """Provede GET s několika pokusy a exponenciálním backoffem."""
    timeout = settings.request_timeout_ms / 1000.0
    last_exc: Exception | None = None
    for attempt in range(1, settings.retries + 1):
        try:
            r = session.get(url, timeout=timeout)
            if r.ok:
                return r
            logger.warning("⚠ HTTP %s (pokus %s/%s): %s", r.status_code, attempt, settings.retries, url)
        except requests.RequestException as e:
            last_exc = e
            logger.warning("⚠ chyba GET (pokus %s/%s): %s", attempt, settings.retries, e)
        if attempt < settings.retries:
            time.sleep(min(2 ** attempt * 0.5, 10))
    if last_exc is not None:
        logger.error("✗ GET selhal po %s pokusech: %s (%s)", settings.retries, url, last_exc)
    return None


def _resolve_filename(headers, suggested_name: str) -> str:
    """Určí finální název souboru z hlaviček a textu odkazu."""
    cd_name = parse_cd_filename(
        headers.get("content-disposition") or headers.get("Content-Disposition")
    )
    base_name = sanitize(choose_best_filename(cd_name, suggested_name))
    if not os.path.splitext(base_name)[1]:
        base_name += infer_ext_from_headers(dict(headers), base_name) or ""
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
            dest = target_dir / info.filename
            if not _is_within(target_dir, dest):
                logger.warning("⚠ přeskočen člen mimo cílovou složku (zip-slip): %s", info.filename)
                continue
            if should_skip(dest.name):
                logger.info("⏭ přeskočen člen ZIP (filtr): %s", info.filename)
                continue
            data = zf.read(info)
            outcomes.append(sync_file(dest.parent, dest.name, data))
    return outcomes


def download_file(
    session: requests.Session,
    url: str,
    suggested_name: str,
    target_dir: Path,
    settings: Settings,
    lock: threading.Lock | None = None,
) -> list[Outcome]:
    """Stáhne soubor, vyfiltruje nechtěné a uloží/rozbalí přes sync.

    Je bezpečné volat z více vláken — zápis do ``target_dir`` chrání ``lock``.
    Vrací seznam :class:`Outcome` (u ZIP jeden na každý rozbalený soubor).
    """
    target_dir = Path(target_dir)
    logger.info("→ GET %s", url)

    r = _get_with_retry(session, url, settings)
    if r is None:
        return []

    headers, body = r.headers, r.content
    base_name = _resolve_filename(headers, suggested_name)

    if should_skip(base_name):
        logger.info("⏭ přeskočeno (filtr): %s", base_name)
        return []

    write_lock = lock or threading.Lock()
    with write_lock:
        if base_name.lower().endswith(".zip"):
            try:
                return _extract_zip(body, target_dir)
            except zipfile.BadZipFile:
                logger.warning("⚠ soubor má .zip, ale nejde rozbalit: %s", base_name)
                return []
        return [sync_file(target_dir, base_name, body)]
