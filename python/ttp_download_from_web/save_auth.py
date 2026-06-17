"""Samostatné přihlášení na portál SŽ (uloží stav relace).

Tenký wrapper nad :mod:`ttp_sz.auth`; konfigurace se bere z ``.env``.
Pro běžný běh není potřeba spouštět ručně — ``download_sz.py`` se přihlásí sám.
"""

from __future__ import annotations

import logging
import sys

from ttp_sz.auth import save_auth
from ttp_sz.config import Settings
from ttp_common.logging_setup import setup_logging


def main() -> int:
    setup_logging(logging.INFO)
    try:
        save_auth(Settings.from_env())
        return 0
    except Exception as e:
        logging.getLogger(__name__).error("✗ Přihlášení selhalo: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
