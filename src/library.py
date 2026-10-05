"""World-library projection for UI and host integrations."""

from __future__ import annotations

from dataclasses import asdict

from .discovery import discover_worlds
from .world_model import SaveSource


def list_worlds(sources: tuple[SaveSource, ...]) -> tuple[dict, ...]:
    """Return stable, UI-ready world rows across all configured sources."""
    rows: list[dict] = []
    for source in sorted(sources, key=lambda item: (item.kind, item.source_id)):
        for world in discover_worlds(source):
            row = asdict(world)
            row["source_kind"] = source.kind
            row["actions"] = ("backup", "duplicate", "rename", "restore", "import", "export")
            rows.append(row)
    return tuple(sorted(rows, key=lambda item: (item["display_name"].casefold(), item["world_id"])))
