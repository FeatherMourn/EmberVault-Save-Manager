"""Post-operation validation and rollback helpers."""

from __future__ import annotations

from pathlib import Path
import shutil

from .inspection import inspect_save_root
from .inspection import is_within_root


def validate_copy(source: str | Path, destination: str | Path, expected_files: tuple[str, ...]) -> bool:
    source_report = inspect_save_root(source, expected_files)
    destination_report = inspect_save_root(destination, expected_files)
    if source_report.state != "ready" or destination_report.state != "ready":
        return False
    source_hashes = {item.relative_path: item.sha256 for item in source_report.files}
    destination_hashes = {item.relative_path: item.sha256 for item in destination_report.files}
    return all(destination_hashes.get(name) == source_hashes.get(name) for name in expected_files)


def rollback_directory(current: str | Path, backup: str | Path) -> None:
    current_path = Path(current)
    backup_path = Path(backup)
    if not backup_path.is_dir():
        raise ValueError("Rollback backup does not exist.")
    if current_path.exists():
        shutil.rmtree(current_path)
    shutil.copytree(backup_path, current_path)


def restore_directory(source_backup: str | Path, current: str | Path,
                      current_state_backup: str | Path, approved_root: str | Path) -> bool:
    """Restore a backup only when all paths are inside the approved root."""
    source = Path(source_backup)
    target = Path(current)
    current_backup = Path(current_state_backup)
    root = Path(approved_root)
    for path in (source, target, current_backup):
        if not is_within_root(path, root):
            raise ValueError("Restore path is outside the approved root.")
    if not source.is_dir() or not current_backup.is_dir():
        raise ValueError("Restore requires source and current-state backups.")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    expected = tuple(item.relative_to(source).as_posix() for item in source.rglob("*") if item.is_file())
    return inspect_save_root(source, expected).state == "ready" and inspect_save_root(target, expected).state == "ready"
