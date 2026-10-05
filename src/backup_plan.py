"""Reviewable backup plans; execution remains owned by Control Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .inspection import InspectionReport, is_within_root


@dataclass(frozen=True)
class BackupPlan:
    operation_id: str
    profile_id: str
    source_root: str
    source_files: tuple[dict, ...]
    requested_label: str
    destination_root: str
    expected_files: tuple[str, ...]
    estimated_size: int
    recovery_instructions: str
    no_mutation: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def plan_backup(
    profile_id: str,
    inspection: InspectionReport,
    destination_root: str | Path,
    approved_backup_root: str | Path,
    label: str,
    operation_id: str | None = None,
) -> BackupPlan:
    """Create a validated plan, raising ``ValueError`` for unsafe inputs."""
    if not profile_id.strip():
        raise ValueError("A profile is required.")
    if inspection.state != "ready":
        raise ValueError("Backup planning requires a ready inspection.")
    if not label.strip():
        raise ValueError("A backup label is required.")
    destination = Path(destination_root)
    if not is_within_root(destination, approved_backup_root):
        raise ValueError("The destination must be inside the approved backup root.")
    files = tuple(asdict(item) for item in inspection.files)
    expected = tuple(item.relative_path for item in inspection.files)
    return BackupPlan(
        operation_id=operation_id or f"EV-OP-{uuid4().hex}",
        profile_id=profile_id.strip(),
        source_root=inspection.root,
        source_files=files,
        requested_label=label.strip(),
        destination_root=str(destination),
        expected_files=expected,
        estimated_size=sum(item["size"] or 0 for item in files),
        recovery_instructions="Control Center must verify source and destination hashes before completion.",
    )
