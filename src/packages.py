"""Portable world package export/import with archive path safety."""

from __future__ import annotations

import json
from pathlib import Path
import zipfile

from .inspection import is_within_root
from .world_model import WorldSave


def export_world(world: WorldSave, archive: str | Path) -> None:
    destination = Path(archive)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        manifest = {"format": 1, "world_id": world.world_id, "display_name": world.display_name,
                    "slot": world.slot, "files": list(world.files)}
        bundle.writestr("manifest.json", json.dumps(manifest, sort_keys=True, indent=2))
        root = Path(world.root)
        for name in world.files:
            path = root / name
            if path.is_file():
                bundle.write(path, arcname=f"files/{name}")


def inspect_package(archive: str | Path) -> dict:
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if any(Path(name).is_absolute() or ".." in Path(name).parts for name in names):
            raise ValueError("Package contains an unsafe path.")
        try:
            manifest = json.loads(bundle.read("manifest.json"))
        except (KeyError, ValueError, UnicodeError) as exc:
            raise ValueError("Package has no valid manifest.") from exc
        if manifest.get("format") != 1 or not isinstance(manifest.get("files"), list):
            raise ValueError("Unsupported package manifest.")
        return manifest


def import_world(archive: str | Path, destination: str | Path, approved_root: str | Path) -> dict:
    target = Path(destination)
    if not is_within_root(target, approved_root):
        raise ValueError("Import destination is outside the approved root.")
    manifest = inspect_package(archive)
    target.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as bundle:
        for name in manifest["files"]:
            member = f"files/{name}"
            if member not in bundle.namelist():
                raise ValueError(f"Package is missing expected file: {name}")
            output = target / name
            if not is_within_root(output, target):
                raise ValueError("Package file escapes the destination.")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(bundle.read(member))
    return manifest
