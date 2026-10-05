"""Read-only save inspection and path-safety helpers."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable

from embervault_sdk import ModuleContext

MODULE_ID = "embervault.save-manager"


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def inspect_save_root(context: ModuleContext, approved_root: Path, *, expected_files: Iterable[str] = ()) -> dict[str, Any]:
    """Inspect files beneath an approved root without changing them."""
    root = Path(approved_root).resolve()
    if context.module_id != MODULE_ID or not context.profile_id:
        return {"state": "blocked", "reason": "Save inspection requires a profile-scoped context."}
    if not root.exists() or not root.is_dir():
        return {"state": "blocked", "reason": "Approved save root does not exist or is not a directory."}
    files = []
    unreadable = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix()):
        if not _inside(root, path.resolve()):
            unreadable.append(path.relative_to(root).as_posix())
            continue
        relative = path.relative_to(root).as_posix()
        try:
            data = path.read_bytes()
            stat = path.stat()
            files.append({"relative_path": relative, "size": stat.st_size,
                          "modified_ns": stat.st_mtime_ns,
                          "sha256": hashlib.sha256(data).hexdigest(),
                          "format": path.suffix.lower().lstrip(".") or "unknown"})
        except OSError:
            unreadable.append(relative)
    expected = sorted(set(expected_files))
    discovered = {item["relative_path"] for item in files}
    missing = sorted(path for path in expected if path not in discovered)
    state = "ready" if not unreadable and not missing else "partial"
    return {"state": state, "profile_id": context.profile_id, "root_name": root.name,
            "files": files, "missing_files": missing, "unreadable_files": sorted(unreadable),
            "mutated_files": False}
