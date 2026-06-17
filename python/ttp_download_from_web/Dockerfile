# Base image Playwright/Python obsahuje Chromium i systémové závislosti pro SŽ.
# Verzi slaďte s verzí balíčku playwright v requirements.txt.
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app

# cron pro denní spouštění
RUN apt-get update \
    && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install chromium

COPY . .

# Cron job + spustitelný entrypoint; adresář na logy.
RUN mkdir -p /var/log/ttp \
    && chmod +x entrypoint.sh \
    && crontab crontab

ENTRYPOINT ["./entrypoint.sh"]
