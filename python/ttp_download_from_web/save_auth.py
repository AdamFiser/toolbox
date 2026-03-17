# save_auth.py
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os, sys

PORTAL_URL = "https://provoz.spravazeleznic.cz/Portal/ViewArticle.aspx?oid=524607"
AUTH_STATE_FILE = "auth_spravazeleznic.json"


def save_auth():
    load_dotenv()
    username = os.environ.get("SZ_USERNAME")
    password = os.environ.get("SZ_PASSWORD")
    if not username or not password:
        print("❗ Chybí SZ_USERNAME nebo SZ_PASSWORD v .env")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(PORTAL_URL)

        # Počkat na login formulář a vyplnit přihlašovací údaje
        page.wait_for_selector("input[type='text'], input[name*='UserName']", timeout=15000)
        page.fill("input[type='text'], input[name*='UserName']", username)
        page.fill("input[type='password']", password)

        # DevExpress overlay (dxmodalSys) blokuje standardní click — použijeme JS
        page.evaluate("document.querySelector('input.kogolSubmitButton, input[type=\"submit\"]').click()")

        # Počkat na dokončení přihlášení
        page.wait_for_load_state("networkidle", timeout=30000)

        context.storage_state(path=AUTH_STATE_FILE)
        print(f"OK Ulozeno: {AUTH_STATE_FILE}")
        browser.close()


if __name__ == "__main__":
    save_auth()
