"""Nastavení standardního logování pro celý balíček.

Nahrazuje původní ruční ``log()`` přes ``print``. Zachovává čitelný formát
s časem; volitelně umí zapisovat i do souboru (vhodné pro běh v kontejneru).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(level: int = logging.INFO, logfile: Path | None = None) -> None:
    """Nakonfiguruje kořenový logger s formátem ``HH:MM:SS úroveň zpráva``."""
    handlers: list[logging.Handler] = []

    stream = logging.StreamHandler(sys.stdout)
    handlers.append(stream)

    if logfile is not None:
        logfile.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(logfile, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
        force=True,
    )

    # stdout na Windows nemusí být v UTF-8 — zajistíme emoji/diakritiku v logu.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
