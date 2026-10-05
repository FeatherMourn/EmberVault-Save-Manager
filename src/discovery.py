"""Filesystem discovery for Enshrouded world-save groups."""

from __future__ import annotations

import json
import re
from hashlib import sha256
from pathlib import Path

from .world_model import SaveSource, WorldSave

WORLD_ID = re.compile(r"^[0-9a-fA-F]{8}$")
KNOWN_SLOTS = {
    "3ad85aea": 1, "3bd85c7d": 2, "38d857c4": 3, "39d85957": 4,
    "36d8549e": 5, "37d85631": 6, "34d85178": 7, "35d8530b": 8,
    "32d84e52": 9, "33d84fe5": 10,
}


def _world_id(path: Path) -> str | None:
    name = path.name
    for suffix in ("_info", "-index", ".backup"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name if WORLD_ID.fullmatch(name) else None


def _display_name(root: Path, world_id: str) -> str:
    info = root / f"{world_id}_info"
    try:
        data = json.loads(info.read_text(encoding="utf-8"))
        for key in ("name", "worldName", "displayName"):
            if isinstance(data.get(key), str) and data[key].strip():
                return data[key].strip()
    except (OSError, ValueError, UnicodeError):
        pass
    return f"World {world_id}"


def _active_copy(root: Path, world_id: str) -> int | None:
    try:
        data = json.loads((root / f"{world_id}-index").read_text(encoding="utf-8"))
        latest = data.get("latest")
        return latest if isinstance(latest, int) and 0 <= latest <= 9 else None
    except (OSError, ValueError, UnicodeError):
        return None


def discover_worlds(source: SaveSource) -> tuple[WorldSave, ...]:
    """Discover world groups without changing the source directory."""
    root = Path(source.root)
    if not root.is_dir():
        return tuple()
    groups: dict[str, list[Path]] = {}
    for path in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
        if path.is_file():
            identity = _world_id(path)
            if identity:
                groups.setdefault(identity, []).append(path)
    worlds: list[WorldSave] = []
    for identity in sorted(groups):
        files = tuple(path.name for path in groups[identity])
        primary = next((path for path in groups[identity] if path.name == identity), groups[identity][0])
        health = "ready" if (root / f"{identity}_info").exists() else "partial"
        worlds.append(WorldSave(identity, _display_name(root, identity), KNOWN_SLOTS.get(identity.lower()),
                                source.source_id, str(root), files, primary.name,
                                health, max(path.stat().st_mtime_ns for path in groups[identity]),
                                _active_copy(root, identity)))
    return tuple(worlds)


def rolling_copy_history(source: SaveSource, world_id: str) -> tuple[dict, ...]:
    """Return read-only history metadata for files belonging to one world."""
    root = Path(source.root)
    if not root.is_dir() or not WORLD_ID.fullmatch(world_id):
        return tuple()
    candidates = [path for path in root.iterdir() if path.is_file() and _world_id(path) == world_id]
    history = []
    for path in sorted(candidates, key=lambda item: (item.stat().st_mtime_ns, item.name)):
        data = path.read_bytes()
        history.append({"file": path.name, "relative_path": path.name, "size": len(data),
                        "modified_ns": path.stat().st_mtime_ns, "sha256": sha256(data).hexdigest(),
                        "active": path.name == world_id})
    return tuple(history)
