# save_auth.py
from playwright.sync_api import sync_playwright

PORTAL_URL = "https://provoz.spravazeleznic.cz/Portal/ViewArticle.aspx?oid=524607"
AUTH_STATE_FILE = "auth_spravazeleznic.json"

with sync_playwright() as p:
    # Spustíme viditelný prohlížeč (non-headless), ať se můžeš přihlásit ručně
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()  # čistý kontext bez cookies
    page = context.new_page()
    page.goto(PORTAL_URL)

    print("\n=== Postup ===")
    print("1) V otevřeném okně se přihlas do Portálu SŽ.")
    print("2) Nech načíst cílovou stránku článku (oid=524607).")
    print("3) Jakmile stránka po přihlášení plně naběhne, vrať se do této konzole a stiskni Enter.\n")
    input("Stiskni Enter, až budeš přihlášen a stránka načtená... ")

    # Uložíme cookies + localStorage do souboru
    context.storage_state(path=AUTH_STATE_FILE)
    print(f"Uloženo: {AUTH_STATE_FILE}")

    browser.close()
