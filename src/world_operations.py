"""Preview and guarded execution primitives for world file operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import shutil

from .inspection import is_within_root
from .operation_rules import OperationDecision
from .world_model import WorldSave


@dataclass(frozen=True)
class OperationPreview:
    operation: str
    source: str
    destination: str
    files: tuple[str, ...]
    conflicts: tuple[str, ...]
    estimated_size: int
    requires_backup: bool

    @property
    def allowed(self) -> bool:
        return not self.conflicts


def preview_world_operation(operation: str, world: WorldSave, destination: str | Path) -> OperationPreview:
    target = Path(destination)
    source = Path(world.root)
    conflicts = tuple(item for item in world.files if (target / item).exists()) if target.exists() else tuple()
    sizes = tuple((source / item).stat().st_size for item in world.files if (source / item).is_file())
    return OperationPreview(operation, str(source), str(target), world.files, conflicts,
                             sum(sizes), operation not in {"export"})


def execute_copy(preview: OperationPreview, decision: OperationDecision, approved_root: str | Path) -> None:
    """Execute only an approved, conflict-free copy inside an approved root."""
    if not decision.allowed:
        raise ValueError(decision.reason)
    if not preview.allowed:
        raise ValueError("Preview contains destination conflicts.")
    source = Path(preview.source)
    destination = Path(preview.destination)
    if not is_within_root(destination, approved_root):
        raise ValueError("Destination is outside the approved root.")
    destination.mkdir(parents=True, exist_ok=False)
    for name in preview.files:
        candidate = source / name
        if candidate.is_file():
            shutil.copy2(candidate, destination / name)
    from .recovery import validate_copy
    expected = tuple(name for name in preview.files if (source / name).is_file())
    if not validate_copy(source, destination, expected):
        shutil.rmtree(destination)
        raise ValueError("Destination verification failed; no source files were changed.")


def execute_move(preview: OperationPreview, decision: OperationDecision, approved_root: str | Path) -> None:
    """Move a complete world group after the same preview and root checks."""
    execute_copy(preview, decision, approved_root)
    source = Path(preview.source)
    for name in preview.files:
        candidate = source / name
        if candidate.is_file():
            candidate.unlink()
    if source.is_dir() and not any(source.iterdir()):
        source.rmdir()


def execute_rename_metadata(edit, decision: OperationDecision, approved_root: str | Path) -> None:
    if not decision.allowed:
        raise ValueError(decision.reason)
    from .metadata_editor import apply_world_name
    apply_world_name(edit, approved_root)


def create_timestamped_backup(world: WorldSave, backup_root: str | Path) -> Path:
    root = Path(backup_root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = root / f"{world.world_id}-{stamp}"
    preview = preview_world_operation("backup", world, destination)
    if destination.exists():
        raise ValueError("Backup destination already exists.")
    decision = OperationDecision(True, "Backup approved.", requires_backup=False)
    execute_copy(preview, decision, root)
    return destination


def archive_world(world: WorldSave, archive_root: str | Path, backup_verified: bool,
                  confirmation: str) -> Path:
    """Move a world group into an archive only after explicit confirmation."""
    if not backup_verified:
        raise ValueError("Archiving requires a verified backup.")
    if confirmation != "ARCHIVE WORLD":
        raise ValueError("Explicit archive confirmation is required.")
    source = Path(world.root)
    archive = Path(archive_root) / world.world_id
    if not source.is_dir() or archive.exists():
        raise ValueError("Archive source or destination is invalid.")
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.mkdir()
    for name in world.files:
        path = source / name
        if path.is_file():
            shutil.move(str(path), str(archive / name))
    return archive
