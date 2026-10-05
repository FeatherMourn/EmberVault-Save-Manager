"""Comparative analysis for read-only save-format research."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .blob_inventory import BlobTag, inventory_bytes


@dataclass(frozen=True)
class HeaderComparison:
    record_count: int
    stable_layout: bool
    stable_lengths: bool
    stable_references: bool
    layouts: tuple[tuple[BlobTag, ...], ...]


def compare_headers(payloads: tuple[bytes, ...]) -> HeaderComparison:
    if not payloads:
        raise ValueError("At least one payload is required.")
    layouts = tuple(inventory_bytes(payload) for payload in payloads)
    first = layouts[0]
    same_tags_offsets = all(tuple((item.tag, item.offset) for item in layout) ==
                            tuple((item.tag, item.offset) for item in first) for layout in layouts[1:])
    same_lengths = all(tuple(item.declared_length for item in layout) ==
                       tuple(item.declared_length for item in first) for layout in layouts[1:])
    same_refs = all(tuple(item.reference for item in layout) ==
                    tuple(item.reference for item in first) for layout in layouts[1:])
    return HeaderComparison(len(first), same_tags_offsets, same_lengths, same_refs, layouts)


def compare_files(paths: tuple[str | Path, ...]) -> HeaderComparison:
    return compare_headers(tuple(Path(path).read_bytes() for path in paths))
