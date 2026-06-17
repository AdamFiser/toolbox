"""Rozpoznání verze souboru podle datového suffixu v názvu.

Nová verze TTP tabulky se na webu SŽ pozná tak, že má v názvu změněný datový
suffix ve tvaru ``RRRRMMDD``. Například::

    304C_01_20260415.pdf  ->  304C_01_20260618.pdf

Obě jména označují tutéž *logickou* tabulku (``304C_01``), liší se jen verzí.
Tento modul ze jména extrahuje:

* **logickou identitu** — název bez datového tokenu, normalizovaný pro porovnání,
* **datum verze** — ``datetime.date`` nebo ``None``, pokud token chybí.

Soubory bez rozpoznaného data (např. ``Mapa tratí TTP 14.12.2025.pdf`` s tečkovým
formátem) dostanou ``version_date = None`` a sync je porovná podle přesného názvu.

Modul je bez I/O — plně pokrytelný unit testy.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date

from .naming import nfc, strip_diacritics

# Datový token RRRRMMDD uvozený oddělovačem (_, -, mezera) nebo začátkem stemu.
# Rok 1900–2099, měsíc 01–12, den 01–31. Přesnou validitu (např. 31. 6.) ověří date().
_DATE_TOKEN_RE = re.compile(
    r"(?:^|[_\-\s])((?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))"
)


@dataclass(frozen=True)
class VersionInfo:
    """Výsledek rozboru názvu souboru z hlediska verzování."""

    identity: str
    """Logická identita pro porovnání (název bez data, bez diakritiky, casefold)."""

    version_date: date | None
    """Datum verze z názvu, nebo ``None``, pokud nebylo rozpoznáno."""

    original: str
    """Původní (nezměněný) název souboru."""


def _normalize_identity(stem: str, ext: str) -> str:
    """Sjednotí stem + příponu na tvar vhodný pro robustní porovnání."""
    stem = strip_diacritics(nfc(stem)).casefold().strip()
    # Sjednotíme oddělovače a zbytkové mezery, ať „304C_01 “ == „304C_01“.
    stem = re.sub(r"[_\-\s]+", "_", stem).strip("_")
    return stem + ext.lower()


def parse_version(filename: str) -> VersionInfo:
    """Rozloží název souboru na logickou identitu a datum verze.

    Bere v úvahu *poslední* (nejpravější) datový token v názvu, který tvoří
    platné kalendářní datum; ten se považuje za verzi a z identity se odebere.
    """
    base = os.path.basename(filename or "").strip()
    stem, ext = os.path.splitext(base)

    version_date: date | None = None
    chosen = None
    # Procházíme matche zprava — verzní suffix bývá poslední v názvu.
    for m in reversed(list(_DATE_TOKEN_RE.finditer(stem))):
        token = m.group(1)
        try:
            version_date = date(int(token[0:4]), int(token[4:6]), int(token[6:8]))
        except ValueError:
            continue  # syntakticky 8 číslic, ale nevalidní datum (např. 31. 6.)
        chosen = m
        break

    if chosen is not None:
        # Odebereme datový token i s jeho uvozujícím oddělovačem.
        stem = stem[: chosen.start()] + stem[chosen.end():]

    return VersionInfo(
        identity=_normalize_identity(stem, ext),
        version_date=version_date,
        original=base,
    )
