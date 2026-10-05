"""Conservative, read-only save-format compatibility assessment."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CompatibilityAssessment:
    format_name: str
    version: str | None
    state: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def assess_save_format(path: str | Path) -> CompatibilityAssessment:
    """Classify a file without editing it or assuming unknown versions are safe."""
    target = Path(path)
    suffix = target.suffix.lower()
    if not target.is_file():
        return CompatibilityAssessment("unknown", None, "blocked", "File is missing.")
    if suffix not in {".sav", ".dat", ".json"}:
        return CompatibilityAssessment("unknown", None, "unsupported", "File extension is not in the inspected format set.")
    if suffix == ".json":
        try:
            value = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            return CompatibilityAssessment("json", None, "unreadable", "JSON metadata could not be decoded.")
        version = value.get("format_version") if isinstance(value, dict) else None
        version_text = str(version) if isinstance(version, (str, int)) else None
        return CompatibilityAssessment("json", version_text, "ready" if version_text else "partial",
                                       "Metadata is readable; version is explicit." if version_text else "Metadata is readable but version is unknown.")
    try:
        if target.stat().st_size == 0:
            return CompatibilityAssessment(suffix[1:], None, "partial", "File is empty.")
    except OSError:
        return CompatibilityAssessment(suffix[1:], None, "unreadable", "File metadata could not be read.")
    return CompatibilityAssessment(suffix[1:], None, "partial", "Binary file is present; format version requires fixture-backed research.")
