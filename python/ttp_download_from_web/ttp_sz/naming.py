"""Čisté funkce pro práci s názvy souborů a hlavičkami Content-Disposition.

Modul neobsahuje žádné I/O (žádný ``page``, ``context`` ani ``open``) — díky tomu
je plně pokrytelný unit testy bez Playwrightu.
"""

from __future__ import annotations

import os
import re
import unicodedata
import urllib.parse

# Znaky s českou diakritikou — používá se pro skórování „lepší“ varianty názvu.
DIACRITICS_CHARS = "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"

_INVALID_PATH_CHARS_RE = re.compile(r'[\\/*?"<>|:]')
_WHITESPACE_RE = re.compile(r"\s+")


def sanitize(s: str) -> str:
    """Nahradí znaky nepovolené v názvu souboru a sjednotí bílé znaky."""
    s = _INVALID_PATH_CHARS_RE.sub("_", s or "")
    s = _WHITESPACE_RE.sub(" ", s)
    return s.strip()


def nfc(s: str) -> str:
    """Normalizuje řetězec do Unicode NFC (sjednocení složené/rozložené diakritiky)."""
    return unicodedata.normalize("NFC", s or "")


def strip_diacritics(s: str) -> str:
    """Odstraní diakritiku, aby šlo robustně porovnávat „trati“ vs „tratí“."""
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def diacritics_score(s: str) -> int:
    """Počet znaků s českou diakritikou — vyšší skóre = „bohatší“ varianta názvu."""
    return sum(ch in DIACRITICS_CHARS for ch in (s or ""))


def parse_cd_filename(header: str | None) -> str | None:
    """Vytáhne jméno souboru z hlavičky Content-Disposition (vč. RFC 5987)."""
    if not header:
        return None

    # RFC 5987: filename*=utf-8''…
    m = re.search(r"filename\*\s*=\s*([^']+)''([^;]+)", header, flags=re.I)
    if m:
        enc = m.group(1).strip().lower()
        raw = m.group(2).strip()
        try:
            return nfc(urllib.parse.unquote(raw, encoding=enc, errors="replace"))
        except Exception:
            return nfc(urllib.parse.unquote(raw, encoding="utf-8", errors="replace"))

    # Klasické filename="…" nebo filename=…
    m = re.search(r'filename\s*=\s*"([^"]+)"', header, flags=re.I)
    if not m:
        m = re.search(r"filename\s*=\s*([^;]+)", header, flags=re.I)
    if m:
        raw_str = m.group(1).strip().strip("'").strip('"')
        cands = [raw_str]
        try:
            b = raw_str.encode("latin-1", errors="replace")
            for enc in ("utf-8", "cp1250", "iso-8859-2"):
                try:
                    cands.append(b.decode(enc))
                except Exception:
                    pass
        except Exception:
            pass
        # Vybereme dekódování s nejbohatší diakritikou (nejčastěji to správné).
        return nfc(max(cands, key=diacritics_score))
    return None


def choose_best_filename(cd_name: str | None, link_text: str | None) -> str:
    """Vybere jméno s lepší diakritikou; při rovnosti delší variantu."""
    a = nfc((cd_name or "").strip())
    b = nfc((link_text or "").strip())
    if not a and b:
        return b
    if not b and a:
        return a
    if diacritics_score(b) > diacritics_score(a):
        return b
    if diacritics_score(a) > diacritics_score(b):
        return a
    return b if len(b) > len(a) else a


def infer_ext_from_headers(headers: dict, fallback_name: str) -> str:
    """Odvodí příponu z hlaviček (Content-Disposition, Content-Type) nebo názvu."""
    cd = headers.get("content-disposition") or headers.get("Content-Disposition")
    if cd:
        cd_fn = parse_cd_filename(cd)
        if cd_fn:
            ext = os.path.splitext(cd_fn)[1]
            if ext:
                return ext
    ctype = (headers.get("content-type") or headers.get("Content-Type") or "").lower()
    if "zip" in ctype:
        return ".zip"
    if "pdf" in ctype:
        return ".pdf"
    if (fallback_name or "").lower().endswith(".pdf"):
        return ".pdf"
    return ""
