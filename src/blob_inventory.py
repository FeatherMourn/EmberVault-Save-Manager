"""Read-only inventory of tagged sections in Enshrouded KSC1 payloads."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


KNOWN_TAGS = frozenset({"CSTR", "SNAP", "WETR", "USER", "KNOW", "EXTS", "SRSG", "CHNK", "SETG",
                        "CHAR", "COUT", "FOWR"})


@dataclass(frozen=True)
class BlobTag:
    tag: str
    offset: int
    declared_length: int | None = None
    reference: str | None = None


def inventory_bytes(payload: bytes) -> tuple[BlobTag, ...]:
    if not payload.startswith(b"KSC1"):
        raise ValueError("Unsupported save container header.")
    found: list[BlobTag] = []
    for offset in range(0, len(payload) - 3):
        candidate = payload[offset:offset + 4].decode("ascii", errors="ignore")
        if candidate in KNOWN_TAGS:
            length = int.from_bytes(payload[offset + 4:offset + 8], "little") if offset + 8 <= len(payload) else None
            reference = payload[offset + 8:offset + 12].hex() if offset + 12 <= len(payload) else None
            found.append(BlobTag(candidate, offset, length, reference))
    return tuple(found)


def inventory_file(path: str | Path) -> tuple[BlobTag, ...]:
    return inventory_bytes(Path(path).read_bytes())
