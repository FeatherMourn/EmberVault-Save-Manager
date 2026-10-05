"""Conservative character-container discovery.

Character payloads are treated as opaque until a verified parser and fixtures
exist. This supports inventory and transfer workflows without corrupting data.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

from .inspection import is_within_root


@dataclass(frozen=True)
class CharacterContainer:
    path: str
    index_path: str | None
    size: int
    state: str


def discover_character_container(root: str | Path) -> CharacterContainer | None:
    base = Path(root)
    payload = base / "characters"
    index = base / "characters-index"
    if not payload.is_file():
        return None
    try:
        size = payload.stat().st_size
    except OSError:
        return CharacterContainer(str(payload), str(index) if index.exists() else None, 0, "unreadable")
    return CharacterContainer(str(payload), str(index) if index.is_file() else None, size,
                              "ready" if index.is_file() else "partial")


def character_edit_supported() -> bool:
    """Return false until the character payload format has a verified parser."""
    return False


def reject_character_edit() -> None:
    raise ValueError("Character editing is not supported until the payload format is verified.")


def export_character(container: CharacterContainer, destination: str | Path) -> Path:
    source = Path(container.path)
    target = Path(destination)
    if not source.is_file():
        raise ValueError("Character container is unavailable.")
    if target.exists():
        raise ValueError("Character export destination already exists.")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def import_character(package: str | Path, destination: str | Path,
                     approved_root: str | Path) -> Path:
    source = Path(package)
    target = Path(destination)
    if not source.is_file():
        raise ValueError("Character package is unavailable.")
    if not is_within_root(target, approved_root):
        raise ValueError("Character destination is outside the approved root.")
    if target.exists():
        raise ValueError("Character destination already exists.")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target
