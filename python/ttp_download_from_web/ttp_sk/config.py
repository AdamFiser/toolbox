"""Konfigurace stahování ŽSR (z ``.env``).

ŽSR nevyžaduje přihlášení — stránka je veřejná. Konfiguruje se hlavně cílová
síťová složka a míra paralelismu.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_PAGE_URL = "https://www.zsr.sk/dopravcovia/infrastruktura/tabulky-tratovych-pomerov/"
DEFAULT_SITE_ROOT = "https://www.zsr.sk"


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


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

        target = os.environ.get("SK_TARGET_DIR", "").strip()
        if not target:
            target = str(Path("SK_TTP") / datetime.now().strftime("%Y%m%d"))

        return cls(
            page_url=os.environ.get("SK_PAGE_URL", DEFAULT_PAGE_URL).strip(),
            site_root=os.environ.get("SK_SITE_ROOT", DEFAULT_SITE_ROOT).strip(),
            target_dir=Path(target),
            workers=max(1, _env_int("SK_DOWNLOAD_WORKERS", 6)),
            request_timeout_ms=_env_int("SK_REQUEST_TIMEOUT_MS", 30000),
            retries=_env_int("SK_RETRIES", 3),
        )
