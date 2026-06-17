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

## Konfigurace (CZ)

Zkopírujte `.env.example` na `.env` a vyplňte:

| Proměnná | Význam | Výchozí |
|----------|--------|---------|
| `SZ_USERNAME`, `SZ_PASSWORD` | přihlášení na portál SŽ | – (povinné) |
| `SZ_TARGET_DIR` | cílová síťová složka | `SZ_TTP/<datum>` (fallback) |
| `SZ_BASE_TTP_URL` | kořen TTP v menu | portál SŽ, oid=5931 |
| `SZ_LOGIN_URL` | přihlašovací stránka | portál SŽ, oid=524607 |
| `SZ_AUTH_STATE_FILE` | dočasný stav přihlášení | `auth_spravazeleznic.json` |
| `SZ_HEADLESS` | běh prohlížeče bez okna | `true` |
| `SZ_SKIP_EXISTING` | přeskakovat již aktuální soubory | `true` |
| `SZ_THROTTLE` | prodleva mezi požadavky (s) | `0.05` |
| `SZ_REQUEST_TIMEOUT_MS` | timeout požadavku (ms) | `30000` |
| `SZ_RETRIES` | počet pokusů při chybě | `3` |

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

## Vývoj a testy

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Logika je rozdělená do balíčku `ttp_sz/` (čisté funkce `naming`, `versioning`,
`filters`, `sync` jsou plně pokryté unit testy bez prohlížeče).
