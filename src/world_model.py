"""Logical Enshrouded world and save-source models."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SaveSource:
    source_id: str
    kind: str
    root: str
    writable: bool
    status: str = "unknown"


@dataclass(frozen=True)
class WorldSave:
    world_id: str
    display_name: str
    slot: int | None
    source_id: str
    root: str
    files: tuple[str, ...]
    active_file: str | None
    health: str
    modified_ns: int | None = None
    active_copy: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def validate_world(world: WorldSave) -> None:
    if not world.world_id.strip():
        raise ValueError("A world ID is required.")
    if not world.display_name.strip():
        raise ValueError("A world display name is required.")
    if world.slot is not None and not 1 <= world.slot <= 10:
        raise ValueError("World slot must be between 1 and 10.")
    if not world.files:
        raise ValueError("A world must contain at least one file.")
    if world.active_file is not None and world.active_file not in world.files:
        raise ValueError("The active file must belong to the world.")
