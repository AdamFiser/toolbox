"""Spustí oba downloadery TTP (SŽ i ŽSR) za sebou.

Vhodné pro automatizovaný (např. cron) běh v kontejneru. Selhání jednoho
downloaderu nezabrání spuštění druhého; návratový kód je nenulový, pokud
selhal aspoň jeden.
"""

from __future__ import annotations

import logging
import os
import sys

from dotenv import load_dotenv

from ttp_common.logging_setup import setup_logging


def main() -> int:
    setup_logging(logging.INFO)
    log = logging.getLogger("run_all")

    # Při běhu z cronu nejsou proměnné prostředí kontejneru zděděné — entrypoint
    # je uložil do souboru, odkud je načteme (dotenv neexpanduje shell, takže
    # zvládá i hesla se speciálními znaky).
    runtime_env = os.environ.get("RUNTIME_ENV_FILE", "/app/container.env")
    if os.path.exists(runtime_env):
        load_dotenv(runtime_env)

    rc = 0

    log.info("═══ TTP SŽ ═══")
    try:
        from ttp_sz.config import Settings
        from ttp_sz.crawler import run as run_sz

        run_sz(Settings.from_env())
    except Exception as e:
        log.error("✗ SŽ selhalo: %s", e)
        rc = 1

    log.info("═══ TTP ŽSR ═══")
    try:
        from ttp_sk.config import SkSettings
        from ttp_sk.run import run as run_sk

        run_sk(SkSettings.from_env())
    except Exception as e:
        log.error("✗ ŽSR selhalo: %s", e)
        rc = 1

    log.info("═══ Hotovo (návratový kód %s) ═══", rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
