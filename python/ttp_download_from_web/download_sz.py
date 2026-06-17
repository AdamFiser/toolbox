"""Entrypoint pro stahování a synchronizaci TTP SŽ.

Konfigurace se načítá z ``.env`` (viz ``.env.example``). Veškerá logika žije
v balíčku :mod:`ttp_sz`.
"""

from __future__ import annotations

import logging
import sys

from ttp_sz.config import Settings
from ttp_sz.crawler import run
from ttp_common.logging_setup import setup_logging


def main() -> int:
    setup_logging(logging.INFO)
    log = logging.getLogger(__name__)
    try:
        settings = Settings.from_env()
        run(settings)
        return 0
    except Exception as e:
        log.error("✗ Běh selhal: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
