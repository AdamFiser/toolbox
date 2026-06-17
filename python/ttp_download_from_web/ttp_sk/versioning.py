"""Rozpoznání verze tabulky ŽSR z textu odkazu.

Na webu ŽSR se tabulka neidentifikuje datem, ale **číslem změny** v textu
odkazu, např.::

    TTP 101 A zmena č. 32

Logická identita je tedy ``TTP 101 A`` a verze je číslo změny ``32``. Na stránce
se může objevit více verzí téže tratě (např. ``TTP 106 D`` se změnou 82 i 84) —
vybírá se nejvyšší číslo změny.

Modul je bez I/O — plně pokrytelný unit testy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# "TTP <číslo> <písmeno> ... <číslo změny>" — písmeno je volitelné,
# číslo změny je poslední číslo v textu (za "zmena č.").
_LINK_RE = re.compile(
    r"^TTP\s+(\d+)\s*([A-Za-z])?\b.*?(\d+)\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SkTable:
    """Tabulka ŽSR rozpoznaná z textu odkazu."""

    identity: str       # logická identita, např. "TTP 101 A"
    change: int         # číslo změny (verze)
    filename: str       # stabilní název souboru pro cíl, např. "TTP 101 A.pdf"
    text: str           # původní text odkazu


def parse_sk_link(text: str) -> SkTable | None:
    """Rozloží text odkazu na identitu a číslo změny; ``None`` při neshodě."""
    t = " ".join((text or "").split())
    m = _LINK_RE.match(t)
    if not m:
        return None
    num, letter, change = m.group(1), m.group(2), m.group(3)
    identity = f"TTP {num}" + (f" {letter.upper()}" if letter else "")
    return SkTable(
        identity=identity,
        change=int(change),
        filename=f"{identity}.pdf",
        text=t,
    )


def select_latest(tables: list[SkTable]) -> list[SkTable]:
    """Pro každou identitu ponechá jen tabulku s nejvyšším číslem změny."""
    best: dict[str, SkTable] = {}
    for tbl in tables:
        cur = best.get(tbl.identity)
        if cur is None or tbl.change > cur.change:
            best[tbl.identity] = tbl
    return list(best.values())
