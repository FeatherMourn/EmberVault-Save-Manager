"""Read-only character record comparison reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .blob_inventory import BlobTag, inventory_bytes


@dataclass(frozen=True)
class RecordGroup:
    ordinal: int
    tag: str
    reference: str | None
    lengths: tuple[int | None, ...]
    stable_length: bool


@dataclass(frozen=True)
class CharacterInspection:
    file_count: int
    record_count: int
    stable_layout: bool
    records: tuple[RecordGroup, ...]


def inspect_character_payloads(payloads: tuple[bytes, ...]) -> CharacterInspection:
    if not payloads:
        raise ValueError("At least one character payload is required.")
    layouts = tuple(inventory_bytes(payload) for payload in payloads)
    first = layouts[0]
    records = []
    for ordinal, reference_record in enumerate(first):
        corresponding = tuple(layout[ordinal] for layout in layouts if ordinal < len(layout))
        lengths = tuple(item.declared_length for item in corresponding)
        records.append(RecordGroup(ordinal, reference_record.tag, reference_record.reference,
                                   lengths, len(set(lengths)) <= 1))
    stable_layout = all(tuple((item.tag, item.offset, item.reference) for item in layout) ==
                        tuple((item.tag, item.offset, item.reference) for item in first)
                        for layout in layouts[1:])
    return CharacterInspection(len(payloads), len(first), stable_layout, tuple(records))


def inspect_character_files(paths: tuple[str | Path, ...]) -> CharacterInspection:
    return inspect_character_payloads(tuple(Path(path).read_bytes() for path in paths))
