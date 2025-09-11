# ttp_download_from_web

Program pro stahování tabulky traťových poměrů TTP z webu manažera infrastruktury:
- CZ - Správa železnic  (vyžaduje přihlašovací údaje)
- SK - Železnice Slovenskej republiky

## Požadavky
- Python 3.8+
- `pip install -r requirements.txt`

## SŽ
1. Spustit `python save_auth.py`, přihlásit se
2. Spustit `python download_cz.py`

## ŽSR
1. Spustit `python download_sk.py`