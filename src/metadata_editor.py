"""Validated, narrow editing of world metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MetadataEdit:
    path: str
    field: str
    old_value: str | None
    new_value: str


def preview_world_name(path: str | Path, new_name: str) -> MetadataEdit:
    metadata_path = Path(path)
    if not new_name.strip():
        raise ValueError("World name cannot be empty.")
    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise ValueError("World metadata is unreadable JSON.") from exc
    if not isinstance(data, dict):
        raise ValueError("World metadata must be a JSON object.")
    current = data.get("name")
    if current is not None and not isinstance(current, str):
        raise ValueError("World metadata name is not text.")
    return MetadataEdit(str(metadata_path), "name", current, new_name.strip())


def apply_world_name(edit: MetadataEdit, approved_root: str | Path) -> None:
    metadata_path = Path(edit.path).resolve()
    root = Path(approved_root).resolve()
    try:
        metadata_path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Metadata path is outside the approved root.") from exc
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    data[edit.field] = edit.new_value
    metadata_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
