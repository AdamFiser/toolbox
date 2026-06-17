"""Idempotentní zápis souborů do cílové (síťové) složky.

Cíl: do sdílené složky se zapíší **jen reálné změny**. Každý zápis spouští
distribuci souboru do tabletů strojvedoucích, takže zbytečné přepisy (identický
obsah) jsou nežádoucí.

Pravidla:

* **Datovaný soubor** (rozpoznán suffix ``RRRRMMDD``): pokud je na cíli verze se
  stejnou logickou identitou a stejným nebo novějším datem → přeskočit. Jinak
  zapsat novou a smazat starší verze téže identity (drží se „jedna aktuální
  verze“).
* **Nedatovaný soubor**: porovná se obsah — identický → přeskočit, jinak zapsat.

Rozhodnutí pro datované soubory je čistá funkce (:func:`plan_for_dated`),
oddělená od I/O kvůli testovatelnosti.
"""

from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .versioning import VersionInfo, parse_version

logger = logging.getLogger(__name__)


class Action(str, Enum):
    """Co se má se souborem na cíli stát."""

    WRITE = "write"      # nový soubor (na cíli nic kolidujícího není)
    REPLACE = "replace"  # zapsat a smazat starší verze téže identity
    SKIP = "skip"        # neukládat (cíl má aktuální/identický)


@dataclass(frozen=True)
class Plan:
    """Plán zápisu pro jeden soubor."""

    action: Action
    remove: list[str] = field(default_factory=list)  # basename starých verzí ke smazání
    reason: str = ""


@dataclass(frozen=True)
class Outcome:
    """Výsledek skutečného zápisu (pro audit, co se poslalo do tabletů)."""

    action: Action
    path: Path
    removed: list[Path] = field(default_factory=list)
    reason: str = ""


def plan_for_dated(new: VersionInfo, existing: list[VersionInfo]) -> Plan:
    """Rozhodne o zápisu datovaného souboru vůči existujícím v cílové složce.

    Čistá funkce — bez I/O. ``existing`` je seznam již přítomných souborů
    (jejich :class:`VersionInfo`) v tomtéž cílovém adresáři.
    """
    same = [e for e in existing if e.identity == new.identity]
    dated = [e for e in same if e.version_date is not None]

    # Je na cíli aktuální nebo novější verze? Pak nic neděláme.
    if any(e.version_date >= new.version_date for e in dated):
        return Plan(Action.SKIP, [], "na cíli je aktuální nebo novější verze")

    # Zapíšeme novou a smažeme všechny starší varianty téže identity.
    remove = [e.original for e in same if e.original != new.original]
    action = Action.REPLACE if remove else Action.WRITE
    return Plan(action, remove, "nová verze")


def _atomic_write(data: bytes, target_path: Path) -> None:
    """Zapíše soubor atomicky (přes dočasný soubor + os.replace) ve stejné složce."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(target_path.parent), suffix=".part")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, target_path)
    except BaseException:
        # Úklid dočasného souboru při jakémkoli selhání.
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def sync_file(target_dir: Path, filename: str, data: bytes) -> Outcome:
    """Idempotentně uloží ``data`` pod ``filename`` do ``target_dir``.

    Zapisuje jen reálné změny; vrací :class:`Outcome` popisující, co se stalo.
    """
    target_dir = Path(target_dir)
    new = parse_version(filename)
    target_path = target_dir / filename

    if new.version_date is not None:
        existing = _existing_versions(target_dir)
        plan = plan_for_dated(new, existing)

        if plan.action is Action.SKIP:
            logger.info("⏭ přeskočeno (%s): %s", plan.reason, filename)
            return Outcome(Action.SKIP, target_path, [], plan.reason)

        removed: list[Path] = []
        _atomic_write(data, target_path)
        for name in plan.remove:
            old = target_dir / name
            try:
                old.unlink()
                removed.append(old)
            except OSError as e:
                logger.warning("⚠ nelze smazat starou verzi %s: %s", old, e)

        verb = "nahrazeno" if plan.action is Action.REPLACE else "uloženo"
        logger.info("✅ %s: %s", verb, filename)
        return Outcome(plan.action, target_path, removed, plan.reason)

    # Nedatovaný soubor — rozhodujeme podle obsahu.
    if target_path.exists() and _same_content(target_path, data):
        logger.info("⏭ přeskočeno (beze změny): %s", filename)
        return Outcome(Action.SKIP, target_path, [], "beze změny")

    existed = target_path.exists()
    _atomic_write(data, target_path)
    action = Action.REPLACE if existed else Action.WRITE
    logger.info("✅ %s: %s", "nahrazeno" if existed else "uloženo", filename)
    return Outcome(action, target_path, [], "změna obsahu" if existed else "nový soubor")


def _existing_versions(target_dir: Path) -> list[VersionInfo]:
    """Načte VersionInfo všech souborů přímo v ``target_dir`` (nerekurzivně)."""
    if not target_dir.exists():
        return []
    return [
        parse_version(p.name)
        for p in target_dir.iterdir()
        if p.is_file()
    ]


def _same_content(path: Path, data: bytes) -> bool:
    """Porovná obsah souboru s ``data`` (krátké TTP soubory — přímé porovnání)."""
    try:
        return path.read_bytes() == data
    except OSError:
        return False
