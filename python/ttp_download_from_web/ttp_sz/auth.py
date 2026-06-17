"""Přihlášení na portál SŽ a uložení stavu relace.

Stav relace (``storage_state``) je pouze dočasný — uchovává přihlášení mezi
přihlašovacím krokem a stahováním. Orchestrace ho na začátku běhu smaže
(vynutí čerstvé přihlášení) a po dokončení opět odstraní.
"""

from __future__ import annotations

import logging

from playwright.sync_api import sync_playwright

from .config import Settings

logger = logging.getLogger(__name__)


def save_auth(settings: Settings) -> None:
    """Přihlásí se přihlašovacími údaji z konfigurace a uloží stav relace."""
    settings.require_credentials()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=settings.headless)
        context = browser.new_context()
        page = context.new_page()
        page.goto(settings.login_url)

        # Počkat na login formulář a vyplnit přihlašovací údaje.
        page.wait_for_selector(
            "input[type='text'], input[name*='UserName']", timeout=15000
        )
        page.fill("input[type='text'], input[name*='UserName']", settings.username)
        page.fill("input[type='password']", settings.password)

        # DevExpress overlay (dxmodalSys) blokuje standardní click — použijeme JS.
        page.evaluate(
            "document.querySelector('input.kogolSubmitButton, input[type=\"submit\"]').click()"
        )

        # Počkat na dokončení přihlášení.
        page.wait_for_load_state("networkidle", timeout=30000)

        context.storage_state(path=str(settings.auth_state_file))
        logger.info("Stav přihlášení uložen: %s", settings.auth_state_file)
        browser.close()
