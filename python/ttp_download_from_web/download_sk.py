"""Entrypoint pro stahování a synchronizaci TTP ŽSR (SK).

Konfigurace se načítá z ``.env`` (viz ``.env.example``). Veškerá logika žije
v balíčku :mod:`ttp_sk`.
"""

from __future__ import annotations

import logging
import sys

from ttp_common.logging_setup import setup_logging
from ttp_sk.config import SkSettings
from ttp_sk.run import run


def main() -> int:
    setup_logging(logging.INFO)
    log = logging.getLogger(__name__)
    try:
        settings = SkSettings.from_env()
        run(settings)
        return 0
    except Exception as e:
        log.error("✗ Běh selhal: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
