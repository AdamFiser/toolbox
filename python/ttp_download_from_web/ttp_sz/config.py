"""Konfigurace stahování načítaná z prostředí (``.env``).

Veškerá nastavení žijí na jednom místě a sdílí je jak stahovací skript, tak
přihlašovací krok (``auth``). Citlivé údaje (přihlášení) a provozní cesty se
nezapisují do kódu, ale do ``.env`` (mimo git).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Výchozí hodnoty — přepsatelné přes .env.
DEFAULT_BASE_TTP_URL = "https://provoz.spravazeleznic.cz/Portal/ViewArticle.aspx?oid=5931"
DEFAULT_LOGIN_URL = "https://provoz.spravazeleznic.cz/Portal/ViewArticle.aspx?oid=524607"
DEFAULT_AUTH_STATE_FILE = "auth_spravazeleznic.json"


def _env_bool(name: str, default: bool) -> bool:
    """Načte boolean z prostředí; akceptuje 1/true/yes/on (case-insensitive)."""
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "ano"}


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Neměnná konfigurace jednoho běhu stahování."""

    username: str
    password: str
    base_ttp_url: str
    login_url: str
    auth_state_file: Path
    target_dir: Path
    headless: bool
    skip_existing: bool
    throttle: float
    request_timeout_ms: int
    retries: int

    @classmethod
    def from_env(cls) -> "Settings":
        """Sestaví konfiguraci z proměnných prostředí (po načtení ``.env``)."""
        load_dotenv()

        target = os.environ.get("SZ_TARGET_DIR", "").strip()
        if not target:
            # Fallback pro lokální běh bez síťové cesty: SZ_TTP/<datum>.
            target = str(Path("SZ_TTP") / datetime.now().strftime("%Y%m%d"))

        return cls(
            username=os.environ.get("SZ_USERNAME", "").strip(),
            password=os.environ.get("SZ_PASSWORD", "").strip(),
            base_ttp_url=os.environ.get("SZ_BASE_TTP_URL", DEFAULT_BASE_TTP_URL).strip(),
            login_url=os.environ.get("SZ_LOGIN_URL", DEFAULT_LOGIN_URL).strip(),
            auth_state_file=Path(
                os.environ.get("SZ_AUTH_STATE_FILE", DEFAULT_AUTH_STATE_FILE).strip()
            ),
            target_dir=Path(target),
            headless=_env_bool("SZ_HEADLESS", True),
            skip_existing=_env_bool("SZ_SKIP_EXISTING", True),
            throttle=_env_float("SZ_THROTTLE", 0.05),
            request_timeout_ms=_env_int("SZ_REQUEST_TIMEOUT_MS", 30000),
            retries=_env_int("SZ_RETRIES", 3),
        )

    def require_credentials(self) -> None:
        """Ověří, že jsou nastaveny přihlašovací údaje; jinak vyhodí výjimku."""
        if not self.username or not self.password:
            raise RuntimeError(
                "Chybí SZ_USERNAME nebo SZ_PASSWORD v .env"
            )
