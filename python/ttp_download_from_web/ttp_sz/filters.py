"""Pravidla pro vyřazení souborů ze stahování.

Filtry pracují jen s názvem souboru — žádné I/O — a jsou tedy plně testovatelné.
Používají se na dvou místech: orientačně už nad textem odkazu a pak definitivně
nad názvem z hlavičky Content-Disposition.
"""

from __future__ import annotations

import os
import re

from .naming import strip_diacritics

# Suffix "_xml" na stemu názvu (typicky *_xml.zip) — XML varianty nestahujeme.
_XML_SUFFIX_RE = re.compile(r"_xml$", re.IGNORECASE)

# Názvy větví menu, které se ignorují celé.
EXCLUDED_MENU_TITLES = {"xml"}


def is_xml_suffix(filename: str) -> bool:
    """True, pokud má název souboru suffix ``_xml`` na stemu (např. ``xxx_xml.zip``)."""
    base = os.path.basename(filename or "").strip()
    if not base:
        return False
    stem, _ext = os.path.splitext(base)
    if stem and _XML_SUFFIX_RE.search(stem):
        return True
    return bool(_XML_SUFFIX_RE.search(base))


def is_xml(filename: str) -> bool:
    """True, pokud je soubor XML — buď příponou ``.xml``, nebo suffixem ``_xml``."""
    base = os.path.basename(filename or "").strip()
    if not base:
        return False
    _stem, ext = os.path.splitext(base)
    if ext.lower() == ".xml":
        return True
    return is_xml_suffix(base)


def is_body_trati_ttp_zip(filename: str) -> bool:
    """True, pokud jde o ZIP, jehož název (bez přípony) končí na „Body tratí TTP“.

    Porovnání je robustní vůči diakritice a velikosti písmen.
    """
    base = os.path.basename(filename or "").strip()
    if not base:
        return False
    stem, ext = os.path.splitext(base)
    if ext.lower() != ".zip":
        return False

    stem_norm = strip_diacritics(stem).casefold().strip()
    target = strip_diacritics("Body tratí TTP").casefold()
    return stem_norm.endswith(target)


def should_skip(filename: str) -> bool:
    """Sjednocené rozhodnutí, zda soubor vynechat (XML nebo Body tratí TTP)."""
    return is_xml(filename) or is_body_trati_ttp_zip(filename)


def is_excluded_menu_item(label: str | None, path: list[str] | None) -> bool:
    """True, pokud položka menu (nebo některý její předek) patří do vyřazených větví."""
    if (label or "").strip().lower() in EXCLUDED_MENU_TITLES:
        return True
    for p in path or []:
        if (p or "").strip().lower() in EXCLUDED_MENU_TITLES:
            return True
    return False
