"""Safety rules for world-management operations."""

from __future__ import annotations

from dataclasses import dataclass

from .world_model import SaveSource, WorldSave, validate_world


@dataclass(frozen=True)
class OperationDecision:
    allowed: bool
    reason: str
    requires_backup: bool = True
    requires_preview: bool = True


MUTATING_OPERATIONS = frozenset({"duplicate", "rename", "move", "import", "restore", "rollback", "edit"})


def authorize_operation(operation: str, world: WorldSave, source: SaveSource, game_running: bool) -> OperationDecision:
    try:
        validate_world(world)
    except ValueError as exc:
        return OperationDecision(False, str(exc))
    if operation not in MUTATING_OPERATIONS:
        return OperationDecision(False, "Unsupported world operation.", False, False)
    if game_running:
        return OperationDecision(False, "Close Enshrouded before changing a world.")
    if not source.writable:
        return OperationDecision(False, "The selected save source is not writable.")
    if source.status != "ready":
        return OperationDecision(False, "The selected save source is not ready.")
    return OperationDecision(True, "Operation may proceed to backup and preview.")
