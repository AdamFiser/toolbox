#!/bin/sh
# Spouštěč kontejneru: připraví prostředí pro cron a spustí cron daemon.
set -e

# Cron nedědí proměnné prostředí kontejneru — uložíme je do souboru, který si
# run_all.py načte přes dotenv (viz RUNTIME_ENV_FILE).
printenv > /app/container.env

# Volitelně spustit jeden běh ihned po startu (užitečné pro ověření nasazení).
if [ "${RUN_ON_START:-false}" = "true" ]; then
    echo "RUN_ON_START=true → spouštím stahování ihned…"
    cd /app && python run_all.py || true
fi

echo "Spouštím cron — denní běh dle crontab. Logy: /var/log/ttp/run.log"
exec cron -f
