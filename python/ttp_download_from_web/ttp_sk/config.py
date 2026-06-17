"""Konfigurace stahování ŽSR (z ``.env``).

Společné provozní parametry (``TARGET_DIR``, ``RETRIES`` …) se čtou sdíleně
z :mod:`ttp_common.config`; zde žijí jen údaje specifické pro ŽSR (URL stránky).
ŽSR nevyžaduje přihlášení.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from ttp_common.config import env_int, env_str, resolve_target

DEFAULT_PAGE_URL = "https://www.zsr.sk/dopravcovia/infrastruktura/tabulky-tratovych-pomerov/"
DEFAULT_SITE_ROOT = "https://www.zsr.sk"
DEFAULT_SUBDIR = "TTP ŽSR"


@dataclass(frozen=True)
class SkSettings:
    """Neměnná konfigurace jednoho běhu stahování ŽSR."""

    page_url: str
    site_root: str
    target_dir: Path
    workers: int
    request_timeout_ms: int
    retries: int

    @classmethod
    def from_env(cls) -> "SkSettings":
        load_dotenv()
        return cls(
            page_url=env_str("SK_PAGE_URL", DEFAULT_PAGE_URL),
            site_root=env_str("SK_SITE_ROOT", DEFAULT_SITE_ROOT),
            target_dir=resolve_target(env_str("SK_SUBDIR", DEFAULT_SUBDIR)),
            workers=max(1, env_int("DOWNLOAD_WORKERS", 6)),
            request_timeout_ms=env_int("REQUEST_TIMEOUT_MS", 30000),
            retries=env_int("RETRIES", 3),
        )
