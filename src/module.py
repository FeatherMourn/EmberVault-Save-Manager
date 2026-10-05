from __future__ import annotations

from embervault_sdk import ModuleContext, ModuleResult
from .inspection import inspect_save_root

MODULE_ID = "embervault.save-manager"


def describe() -> dict:
    return {"id": MODULE_ID, "execution": "embedded", "application_state": "managed", "mutates_saves": True}


def inspect(context: ModuleContext, save_root: str, expected_paths: tuple[str, ...] = ()) -> ModuleResult:
    if context.module_id != MODULE_ID or not context.profile_id:
        return ModuleResult("blocked", "Save Manager requires a profile-scoped context.")
    report = inspect_save_root(save_root, expected_paths)
    return ModuleResult(report.state, "Save inspection completed.", report.to_dict())


def plan_backup(context: ModuleContext, label: str) -> ModuleResult:
    if context.module_id != MODULE_ID or not context.profile_id:
        return ModuleResult("blocked", "Save Manager requires a profile-scoped context.")
    if not label.strip():
        return ModuleResult("blocked", "A backup label is required.")
    return ModuleResult("ready", "Save backup prepared.", {"label": label.strip(), "profile_id": context.profile_id})


def plan_restore(context: ModuleContext, source_backup_id: str, current_backup_verified: bool) -> ModuleResult:
    if context.module_id != MODULE_ID or not context.profile_id:
        return ModuleResult("blocked", "Save Manager requires a profile-scoped context.")
    if context.capability_state != "approved" or not context.backup_id:
        return ModuleResult("blocked", "Restore requires an approved operation and verified current-state backup.")
    if not source_backup_id.strip() or not current_backup_verified:
        return ModuleResult("blocked", "Restore requires a selected source backup and verified current-state backup.")
    return ModuleResult("ready", "Save restore prepared.", {
        "source_backup_id": source_backup_id.strip(), "current_backup_id": context.backup_id,
        "profile_id": context.profile_id, "application_state": "backup-gated",
    })
