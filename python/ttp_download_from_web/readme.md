# ttp_download_from_web

Stahování tabulek traťových poměrů (TTP) z webů manažerů infrastruktury:

- **CZ – Správa železnic** (`download_sz.py`, vyžaduje přihlašovací údaje)
- **SK – Železnice Slovenskej republiky** (`download_sk.py`)

Stažené soubory se synchronizují do cílové (síťové) složky tak, aby se zapsaly
**jen reálné změny** — odtud se distribuují do tabletů strojvedoucích.

## Požadavky

- Python 3.8+
- `pip install -r requirements.txt`
- `python -m playwright install chromium` (pro CZ)

## Konfigurace

Zkopírujte `.env.example` na `.env` a vyplňte. Pod společným kořenem
`TARGET_DIR` si každý downloader vytvoří vlastní podsložku (`TTP SŽ`, `TTP ŽSR`).

**Společné parametry:**

| Proměnná | Význam | Výchozí |
|----------|--------|---------|
| `TARGET_DIR` | kořenová cílová složka | `.` (lokální fallback) |
| `HEADLESS` | běh prohlížeče bez okna (SŽ) | `true` |
| `SKIP_EXISTING` | přeskakovat již aktuální soubory | `true` |
| `THROTTLE` | prodleva mezi požadavky (s) | `0.05` |
| `REQUEST_TIMEOUT_MS` | timeout požadavku (ms) | `30000` |
| `RETRIES` | počet pokusů při chybě | `3` |
| `DOWNLOAD_WORKERS` | počet paralelních stahování | `6` |

**Jen SŽ:**

| Proměnná | Význam | Výchozí |
|----------|--------|---------|
| `SZ_USERNAME`, `SZ_PASSWORD` | přihlášení na portál SŽ | – (povinné) |
| `SZ_BASE_TTP_URL` | kořen TTP v menu | portál SŽ, oid=5931 |
| `SZ_LOGIN_URL` | přihlašovací stránka | portál SŽ, oid=524607 |
| `SZ_AUTH_STATE_FILE` | dočasný stav přihlášení | `auth_spravazeleznic.json` |
| `SZ_SUBDIR` | podsložka pod `TARGET_DIR` | `TTP SŽ` |

**Jen ŽSR:**

| Proměnná | Význam | Výchozí |
|----------|--------|---------|
| `SK_PAGE_URL` | stránka se seznamem tabulek | web ŽSR |
| `SK_SITE_ROOT` | kořen webu pro absolutní odkazy | `https://www.zsr.sk` |
| `SK_SUBDIR` | podsložka pod `TARGET_DIR` | `TTP ŽSR` |

## Spuštění

### SŽ (CZ)

```bash
python download_sz.py
```

Skript se sám přihlásí (dočasný stav přihlášení po dokončení smaže), projde menu,
stáhne soubory a do cílové složky zapíše jen změny. Nová verze tabulky se pozná
podle změněného datového suffixu v názvu (`RRRRMMDD`), např.
`304C_01_20260415.pdf` → `304C_01_20260618.pdf`; starší verze se nahradí.

### ŽSR (SK)

```bash
python download_sk.py
```

ŽSR nevyžaduje přihlášení. Verze tabulky se pozná podle **čísla změny** v textu
odkazu (`TTP 101 A zmena č. 32`); pro každou trať se vybere nejvyšší číslo změny
a uloží pod stabilním názvem (`TTP 101 A.pdf`), takže se zapíše jen reálná změna.

## Vývoj a testy

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Logika je rozdělená do balíčků: `ttp_common/` (sdílené — `naming`, `versioning`,
`sync`, `logging_setup`), `ttp_sz/` (SŽ — Playwright, menu, filtry) a `ttp_sk/`
(ŽSR — requests, verzování podle čísla změny). Čisté funkce jsou plně pokryté
unit testy bez sítě a prohlížeče.
