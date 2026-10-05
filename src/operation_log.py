"""Privacy-conscious operation history."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path


@dataclass(frozen=True)
class OperationRecord:
    operation_id: str
    operation: str
    world_id: str
    status: str
    source: str
    destination: str | None
    validation: str
    timestamp: str


def append_record(path: str | Path, record: OperationRecord) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), sort_keys=True) + "\n")


def new_record(operation_id: str, operation: str, world_id: str, status: str,
               source: str, destination: str | None, validation: str) -> OperationRecord:
    return OperationRecord(operation_id, operation, world_id, status, source,
                           destination, validation,
                           datetime.now(timezone.utc).isoformat())


def read_records(path: str | Path) -> tuple[OperationRecord, ...]:
    target = Path(path)
    if not target.exists():
        return tuple()
    records = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(OperationRecord(**json.loads(line)))
    return tuple(records)
