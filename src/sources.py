"""Discovery of common Enshrouded save roots."""

from __future__ import annotations

from pathlib import Path
import re
import hashlib

from .world_model import SaveSource


def discover_sources(server_roots: tuple[str | Path, ...] = ()) -> tuple[SaveSource, ...]:
    user = Path.home()
    candidates = [
        ("local", "local", user / "Saved Games" / "enshrouded"),
    ]
    steam_roots = [Path("C:/Program Files (x86)/Steam")]
    for library_file in Path("C:/Program Files (x86)/Steam/steamapps").glob("libraryfolders.vdf"):
        try:
            text = library_file.read_text(encoding="utf-8", errors="ignore")
            steam_roots.extend(Path(value.replace("\\\\", "\\")) for value in re.findall(r'"path"\s+"([^"]+)"', text))
        except OSError:
            pass
    for steam_root in dict.fromkeys(steam_roots):
        steam_userdata = steam_root / "userdata"
        if steam_userdata.is_dir():
            for account in sorted(steam_userdata.iterdir(), key=lambda item: item.name.casefold()):
                candidates.append((f"steam-cloud-{account.name}-{steam_root.drive or 'library'}", "steam-cloud",
                                   account / "1203620" / "remote"))
    for index, root in enumerate(server_roots, start=1):
        candidates.append((f"server-{index}", "dedicated-server", Path(root)))
    return tuple(
        SaveSource(source_id, kind, str(root), root.is_dir(), "ready" if root.is_dir() else "missing")
        for source_id, kind, root in candidates
    )


def source_fingerprint(root: str | Path) -> dict[str, str]:
    base = Path(root)
    result = {}
    if not base.is_dir():
        return result
    for path in sorted((item for item in base.iterdir() if item.is_file()), key=lambda item: item.name.casefold()):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        result[path.name] = digest
    return result


def compare_sources(left: str | Path, right: str | Path) -> dict:
    left_map, right_map = source_fingerprint(left), source_fingerprint(right)
    names = set(left_map) | set(right_map)
    return {"added": sorted(name for name in names if name not in left_map),
            "removed": sorted(name for name in names if name not in right_map),
            "changed": sorted(name for name in names if name in left_map and name in right_map and left_map[name] != right_map[name]),
            "identical": not any(name not in left_map or name not in right_map or left_map[name] != right_map[name] for name in names)}
