"""Načtení a rozbor stránky ŽSR s tabulkami TTP (requests + BeautifulSoup)."""

from __future__ import annotations

import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from ttp_common.naming import sanitize

from .config import SkSettings
from .versioning import SkTable, parse_sk_link

logger = logging.getLogger(__name__)

_USER_AGENT = "Mozilla/5.0 (compatible; ttp-downloader/1.0)"
_GENERAL_EXTS = (".pdf", ".xlsx")


def discover(settings: SkSettings) -> tuple[list[tuple[SkTable, str]], list[tuple[str, str]]]:
    """Stáhne stránku a vrátí (tabulky s URL, obecné soubory s URL).

    Tabulky se rozpoznají podle textu odkazu (``TTP …``); obecné soubory podle
    přímé přípony (``.pdf``/``.xlsx``).
    """
    r = requests.get(
        settings.page_url,
        timeout=settings.request_timeout_ms / 1000.0,
        headers={"User-Agent": _USER_AGENT},
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    tables: list[tuple[SkTable, str]] = []
    general: list[tuple[str, str]] = []
    seen_general: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = (a["href"] or "").strip()
        if not href:
            continue
        text = a.get_text(strip=True)

        tbl = parse_sk_link(text)
        if tbl is not None:
            tables.append((tbl, urljoin(settings.site_root, href)))
            continue

        if href.lower().endswith(_GENERAL_EXTS):
            url = urljoin(settings.site_root, href)
            if url in seen_general:
                continue
            seen_general.add(url)
            general.append((sanitize(href.split("/")[-1]), url))

    return tables, general
