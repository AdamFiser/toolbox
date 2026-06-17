"""Sdílené čtení konfigurace z prostředí (``.env``).

Společné provozní parametry mají jednotné názvy bez prefixu (``TARGET_DIR``,
``HEADLESS``, ``RETRIES``, …) a sdílí je oba downloadery. Každý downloader si
pod společným kořenem ``TARGET_DIR`` vytváří vlastní podsložku.
"""

from __future__ import annotations

import os
from pathlib import Path


def env_str(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "ano"}


def env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def resolve_target(subdir: str) -> Path:
    """Cílová složka downloaderu = ``TARGET_DIR`` / podsložka.

    Bez nastaveného ``TARGET_DIR`` se použije lokální fallback (relativní cesta).
    """
    root = env_str("TARGET_DIR")
    base = Path(root) if root else Path(".")
    return base / subdir
