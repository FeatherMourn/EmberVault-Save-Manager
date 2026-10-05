"""Read-only save inspection primitives.

This module deliberately has no filesystem mutation operations. Control Center
owns any copy, restore, or rollback execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SaveFileRecord:
    relative_path: str
    kind: str
    size: int | None
    modified_ns: int | None
    sha256: str | None
    format: str | None
    state: str
    error: str | None = None


@dataclass(frozen=True)
class InspectionReport:
    root: str
    state: str
    files: tuple[SaveFileRecord, ...]

    def to_dict(self) -> dict:
        return {"root": self.root, "state": self.state,
                "files": [asdict(item) for item in self.files]}


def is_within_root(candidate: str | Path, approved_root: str | Path) -> bool:
    """Return whether a path resolves inside the approved root."""
    try:
        Path(candidate).resolve(strict=False).relative_to(Path(approved_root).resolve(strict=False))
        return True
    except ValueError:
        return False


def _format_for(path: Path) -> str | None:
    suffix = path.suffix.lower()
    return {".sav": "save", ".dat": "data", ".json": "json"}.get(suffix)


def _file_record(root: Path, path: Path) -> SaveFileRecord:
    relative = path.relative_to(root).as_posix()
    try:
        stat = path.stat()
        digest = sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return SaveFileRecord(relative, "file", stat.st_size, stat.st_mtime_ns,
                              digest.hexdigest(), _format_for(path), "ready")
    except (OSError, PermissionError) as exc:
        return SaveFileRecord(relative, "file", None, None, None,
                              _format_for(path), "unreadable", str(exc))


def inspect_save_root(root: str | Path, expected_paths: Iterable[str] = ()) -> InspectionReport:
    """Inspect *root* without changing it and return stable, sorted metadata."""
    base = Path(root)
    if not base.exists():
        return InspectionReport(str(base), "blocked", tuple())
    if not base.is_dir():
        return InspectionReport(str(base), "unreadable", tuple())

    records = tuple(_file_record(base, path) for path in sorted(
        (candidate for candidate in base.rglob("*") if candidate.is_file()),
        key=lambda item: item.relative_to(base).as_posix().casefold()))
    known = {item.relative_path for item in records}
    missing = [path.replace("\\", "/") for path in expected_paths if path.replace("\\", "/") not in known]
    if missing:
        records += tuple(SaveFileRecord(path, "missing", None, None, None, None, "partial") for path in sorted(missing))
    state = "unreadable" if any(item.state == "unreadable" for item in records) else ("partial" if missing else "ready")
    return InspectionReport(str(base), state, records)

