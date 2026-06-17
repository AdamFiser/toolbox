"""Konfigurace stahování SŽ (z ``.env``).

Společné provozní parametry (``TARGET_DIR``, ``HEADLESS``, ``RETRIES`` …) se
čtou sdíleně z :mod:`ttp_common.config`; zde žijí jen údaje specifické pro SŽ
(přihlášení, URL portálu, stav relace).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from ttp_common.config import env_bool, env_float, env_int, env_str, resolve_target

# Výchozí hodnoty specifické pro SŽ — přepsatelné přes .env.
DEFAULT_BASE_TTP_URL = "https://provoz.spravazeleznic.cz/Portal/ViewArticle.aspx?oid=5931"
DEFAULT_LOGIN_URL = "https://provoz.spravazeleznic.cz/Portal/ViewArticle.aspx?oid=524607"
DEFAULT_AUTH_STATE_FILE = "auth_spravazeleznic.json"
DEFAULT_SUBDIR = "TTP SŽ"


@dataclass(frozen=True)
class Settings:
    """Neměnná konfigurace jednoho běhu stahování SŽ."""

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
    download_workers: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            username=env_str("SZ_USERNAME"),
            password=env_str("SZ_PASSWORD"),
            base_ttp_url=env_str("SZ_BASE_TTP_URL", DEFAULT_BASE_TTP_URL),
            login_url=env_str("SZ_LOGIN_URL", DEFAULT_LOGIN_URL),
            auth_state_file=Path(env_str("SZ_AUTH_STATE_FILE", DEFAULT_AUTH_STATE_FILE)),
            target_dir=resolve_target(env_str("SZ_SUBDIR", DEFAULT_SUBDIR)),
            headless=env_bool("HEADLESS", True),
            skip_existing=env_bool("SKIP_EXISTING", True),
            throttle=env_float("THROTTLE", 0.05),
            request_timeout_ms=env_int("REQUEST_TIMEOUT_MS", 30000),
            retries=env_int("RETRIES", 3),
            download_workers=max(1, env_int("DOWNLOAD_WORKERS", 6)),
        )

    def require_credentials(self) -> None:
        """Ověří, že jsou nastaveny přihlašovací údaje; jinak vyhodí výjimku."""
        if not self.username or not self.password:
            raise RuntimeError("Chybí SZ_USERNAME nebo SZ_PASSWORD v .env")
