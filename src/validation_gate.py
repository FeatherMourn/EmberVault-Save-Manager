"""Explicit gate for future private real-save validation."""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class ValidationGate:
    allowed: bool
    reason: str
    fixture_root: str | None = None
    backup_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def request_validation(explicit_opt_in: bool, game_closed: bool, verified_backup_id: str | None,
                       fixture_root: str | None) -> ValidationGate:
    """Require all safety acknowledgements before any future validation adapter runs."""
    if not explicit_opt_in:
        return ValidationGate(False, "Explicit opt-in is required.")
    if not game_closed:
        return ValidationGate(False, "Enshrouded must be closed before validation.")
    if not verified_backup_id or not verified_backup_id.strip():
        return ValidationGate(False, "A verified backup is required before validation.")
    if not fixture_root or not fixture_root.strip():
        return ValidationGate(False, "An explicitly selected private fixture root is required.")
    return ValidationGate(True, "Validation may be prepared for the selected private fixture.", fixture_root.strip(), verified_backup_id.strip())
