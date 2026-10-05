import unittest
import shutil
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from embervault_sdk import ModuleContext
from src.module import plan_backup, plan_restore
from src.recovery import build_recovery_evidence
from src.compatibility import assess_save_format
from pathlib import Path
from tempfile import TemporaryDirectory
from src.inspection import inspect_save_root, is_within_root
from src.backup_plan import plan_backup as create_backup_plan
from src.operation_rules import authorize_operation
from src.world_model import SaveSource, WorldSave
from src.discovery import discover_worlds
from src.world_operations import archive_world, create_timestamped_backup, execute_copy, execute_move, preview_world_operation
from src.recovery import restore_directory, rollback_directory, validate_copy
from src.metadata_editor import apply_world_name, preview_world_name
from src.library import list_worlds
from src.characters import (character_edit_supported, discover_character_container,
                            export_character, import_character)
from src.cli import main as cli_main
from src.packages import export_world, import_world, inspect_package
from src.ui import (_dispatch_selected, WorldLibraryController, confirm_operation,
                    create_world_library, request_operation_destination)
from src.blob_inventory import inventory_bytes
from src.format_analysis import compare_headers
from src.character_analysis import inspect_character_payloads
from src.operation_log import append_record, new_record, read_records
from src.sources import compare_sources, discover_sources
from src.process_guard import is_game_running


class SaveManagerTests(unittest.TestCase):
    def test_inspection_is_deterministic_and_hashes_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "b.sav").write_bytes(b"two")
            (root / "a.sav").write_bytes(b"one")
            first = inspect_save_root(root).to_dict()
            second = inspect_save_root(root).to_dict()
            self.assertEqual(first, second)
            self.assertEqual([item["relative_path"] for item in first["files"]], ["a.sav", "b.sav"])
            self.assertEqual(first["state"], "ready")

    def test_inspection_reports_missing_expected_file(self):
        with TemporaryDirectory() as directory:
            report = inspect_save_root(directory, ("world.sav",))
            self.assertEqual(report.state, "partial")
            self.assertEqual(report.files[0].state, "partial")

    def test_path_safety_rejects_traversal(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "approved"
            outside = Path(directory) / "outside"
            self.assertTrue(is_within_root(root / "save.sav", root))
            self.assertFalse(is_within_root(root / ".." / outside.name, root))

    def test_backup_plan_is_reviewable_and_has_no_mutation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "saves"
            approved = Path(directory) / "backups"
            root.mkdir()
            approved.mkdir()
            (root / "world.sav").write_bytes(b"save")
            inspection = inspect_save_root(root)
            plan = create_backup_plan("default", inspection, approved / "before-mods", approved,
                                      "before mods", operation_id="EV-OP-TEST")
            self.assertEqual(plan.operation_id, "EV-OP-TEST")
            self.assertEqual(plan.expected_files, ("world.sav",))
            self.assertEqual(plan.estimated_size, 4)
            self.assertTrue(plan.no_mutation)

    def test_backup_plan_rejects_unapproved_destination(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "saves"
            approved = Path(directory) / "backups"
            root.mkdir()
            approved.mkdir()
            (root / "world.sav").write_bytes(b"save")
            with self.assertRaises(ValueError):
                create_backup_plan("default", inspect_save_root(root), Path(directory) / "outside", approved, "test")

    def test_operation_rules_block_running_game_and_allow_safe_operation(self):
        world = WorldSave("world-1", "Meadow", 1, "local", "saves", ("world.sav",), "world.sav", "ready")
        source = SaveSource("local", "local", "saves", True, "ready")
        self.assertFalse(authorize_operation("rename", world, source, True).allowed)
        decision = authorize_operation("rename", world, source, False)
        self.assertTrue(decision.allowed)
        self.assertTrue(decision.requires_backup)

    def test_operation_rules_reject_unwritable_source(self):
        world = WorldSave("world-1", "Meadow", 1, "cloud", "cloud", ("world.sav",), "world.sav", "ready")
        source = SaveSource("cloud", "steam-cloud", "cloud", False, "ready")
        self.assertFalse(authorize_operation("move", world, source, False).allowed)

    def test_discovery_groups_world_files_and_reads_name(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "3ad85aea").write_bytes(b"world")
            (root / "3ad85aea_info").write_text('{"name":"Meadow"}', encoding="utf-8")
            (root / "3ad85aea-index").write_text('{"latest":0}', encoding="utf-8")
            worlds = discover_worlds(SaveSource("local", "local", str(root), True, "ready"))
            self.assertEqual(len(worlds), 1)
            self.assertEqual(worlds[0].display_name, "Meadow")
            self.assertEqual(set(worlds[0].files), {"3ad85aea", "3ad85aea_info", "3ad85aea-index"})
            self.assertEqual(worlds[0].health, "ready")
            self.assertEqual(worlds[0].active_copy, 0)

    def test_discovery_marks_missing_metadata_partial(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "3bd85c7d").write_bytes(b"world")
            worlds = discover_worlds(SaveSource("local", "local", str(root), True, "ready"))
            self.assertEqual(worlds[0].health, "partial")

    def test_discovery_does_not_renumber_unknown_or_missing_slots(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "3bd85c7d").write_bytes(b"world")
            (root / "3bd85c7d_info").write_text('{"name":"Second"}', encoding="utf-8")
            worlds = discover_worlds(SaveSource("local", "local", str(root), True, "ready"))
            self.assertEqual(worlds[0].slot, 2)

    def test_operation_history_records_metadata_without_save_contents(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "operations.jsonl"
            record = new_record("EV-OP-1", "backup", "world-1", "verified", "saves", "backup", "matched")
            append_record(path, record)
            records = read_records(path)
            self.assertEqual(records[0].operation_id, "EV-OP-1")
            self.assertNotIn("world contents", path.read_text(encoding="utf-8"))

    def test_source_discovery_reports_user_and_server_roots_without_mutation(self):
        sources = discover_sources(("Z:/not-a-real-server-save",))
        self.assertTrue(any(source.kind == "local" for source in sources))
        server = next(source for source in sources if source.kind == "dedicated-server")
        self.assertEqual(server.status, "missing")

    def test_source_comparison_reports_cloud_divergence(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); left = root / "left"; right = root / "right"
            left.mkdir(); right.mkdir(); (left / "world").write_bytes(b"one"); (right / "world").write_bytes(b"two")
            (right / "extra").write_bytes(b"extra")
            comparison = compare_sources(left, right)
            self.assertEqual(comparison["changed"], ["world"])
            self.assertEqual(comparison["added"], ["extra"])
            self.assertFalse(comparison["identical"])

    def test_process_guard_accepts_injected_process_names(self):
        self.assertFalse(is_game_running(frozenset({"definitely-not-running.exe"})))

    def test_restore_requires_current_state_backup_and_validates_result(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "source"; current = root / "current"
            current_backup = root / "current-backup"
            for path in (source, current, current_backup): path.mkdir()
            (source / "world.sav").write_bytes(b"restored")
            (current / "world.sav").write_bytes(b"current")
            shutil.copy2(current / "world.sav", current_backup / "world.sav")
            self.assertTrue(restore_directory(source, current, current_backup, root))
            self.assertEqual((current / "world.sav").read_bytes(), b"restored")

    def test_ui_dispatches_selected_action_to_service_callback(self):
        class Table:
            def selection(self):
                return ("world-1",)
        received = []
        _dispatch_selected(Table(), "backup", lambda action, world: received.append((action, world)))
        self.assertEqual(received, [("backup", "world-1")])

    def test_ui_operation_destination_is_not_requested_for_metadata_rename(self):
        self.assertIsNone(request_operation_destination(None, "rename"))

    def test_ui_controller_previews_confirms_and_dispatches_action(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "saves"
            destination = Path(directory) / "backup"
            root.mkdir()
            destination.mkdir()
            (root / "3ad85aea").write_bytes(b"world")
            world = discover_worlds(SaveSource("local", "local", str(root), True, "ready"))[0]
            received = []
            controller = WorldLibraryController(
                None, (SaveSource("local", "local", str(root), True, "ready"),), received.append,
                destination_picker=lambda _parent, _action: str(destination),
                confirmer=lambda _parent, _action, _name, text: "Estimated size" in text,
            )
            request = controller.handle("backup", world.world_id)
            self.assertIsNotNone(request)
            self.assertEqual(received[0].action, "backup")
            self.assertEqual(received[0].preview.estimated_size, 5)

    def test_blob_inventory_is_read_only_and_requires_ksc1(self):
        payload = b"KSC1" + b"EXTS" + b"xxxx" + b"SRSG" + b"CHAR"
        tags = inventory_bytes(payload)
        self.assertEqual([tag.tag for tag in tags], ["EXTS", "SRSG", "CHAR"])
        self.assertEqual(tags[0].declared_length, 2021161080)
        with self.assertRaises(ValueError):
            inventory_bytes(b"not-a-save")

    def test_format_analysis_reports_stable_layout_and_lengths(self):
        first = b"KSC1" + b"CHAR" + (4).to_bytes(4, "little") + b"abcd"
        second = b"KSC1" + b"CHAR" + (4).to_bytes(4, "little") + b"efgh"
        comparison = compare_headers((first, second))
        self.assertEqual(comparison.record_count, 1)
        self.assertTrue(comparison.stable_layout)
        self.assertTrue(comparison.stable_lengths)
        self.assertFalse(comparison.stable_references)

    def test_character_inspection_groups_stable_references_and_length_changes(self):
        first = b"KSC1" + b"CHAR" + (4).to_bytes(4, "little") + b"abcd"
        second = b"KSC1" + b"CHAR" + (8).to_bytes(4, "little") + b"abcd"
        report = inspect_character_payloads((first, second))
        self.assertTrue(report.stable_layout)
        self.assertEqual(report.record_count, 1)
        self.assertFalse(report.records[0].stable_length)

    def test_world_operation_preview_and_guarded_copy(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "saves"
            approved = Path(directory) / "backups"
            root.mkdir(); approved.mkdir()
            (root / "3ad85aea").write_bytes(b"world")
            world = WorldSave("3ad85aea", "Meadow", 1, "local", str(root), ("3ad85aea",), "3ad85aea", "ready")
            preview = preview_world_operation("backup", world, approved / "copy")
            self.assertTrue(preview.allowed)
            decision = authorize_operation("rename", world, SaveSource("local", "local", str(root), True, "ready"), False)
            execute_copy(preview, decision, approved)
            self.assertEqual((approved / "copy" / "3ad85aea").read_bytes(), b"world")

    def test_copy_validation_and_rollback(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"; backup = root / "backup"; current = root / "current"
            source.mkdir(); backup.mkdir(); current.mkdir()
            (source / "world.sav").write_bytes(b"good")
            shutil.copy2(source / "world.sav", backup / "world.sav")
            (current / "world.sav").write_bytes(b"bad")
            self.assertTrue(validate_copy(source, backup, ("world.sav",)))
            rollback_directory(current, backup)
            self.assertEqual((current / "world.sav").read_bytes(), b"good")

    def test_world_metadata_name_preview_and_apply(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "world_info"
            path.write_text('{"name":"Old Name","slot":1}', encoding="utf-8")
            edit = preview_world_name(path, "New Name")
            self.assertEqual(edit.old_value, "Old Name")
            apply_world_name(edit, directory)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["name"], "New Name")

    def test_world_library_returns_stable_ui_rows(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "3ad85aea").write_bytes(b"world")
            (root / "3ad85aea_info").write_text('{"name":"Meadow"}', encoding="utf-8")
            rows = list_worlds((SaveSource("local", "local", str(root), True, "ready"),))
            self.assertEqual(rows[0]["display_name"], "Meadow")
            self.assertIn("backup", rows[0]["actions"])

    def test_character_container_is_discovered_without_parsing_payload(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "characters").write_bytes(b"opaque")
            container = discover_character_container(root)
            self.assertEqual(container.state, "partial")
            self.assertFalse(character_edit_supported())

    def test_character_opaque_export_and_import(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "characters"; exported = root / "exported.bin"
            imported = root / "approved" / "characters"
            source.write_bytes(b"opaque-character")
            container = discover_character_container(root)
            export_character(container, exported)
            import_character(exported, imported, root / "approved")
            self.assertEqual(imported.read_bytes(), b"opaque-character")

    def test_cli_lists_worlds_as_json(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "3ad85aea").write_bytes(b"world")
            (root / "3ad85aea_info").write_text('{"name":"Meadow"}', encoding="utf-8")
            self.assertEqual(cli_main([str(root), "--json"]), 0)

    def test_move_operation_copies_then_removes_source_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"; destination = root / "destination"
            source.mkdir(); destination.mkdir()
            (source / "world.sav").write_bytes(b"world")
            world = WorldSave("world-1", "Meadow", 1, "local", str(source), ("world.sav",), "world.sav", "ready")
            decision = authorize_operation("move", world, SaveSource("local", "local", str(source), True, "ready"), False)
            execute_move(preview_world_operation("move", world, destination / "world"), decision, destination)
            self.assertFalse((source / "world.sav").exists())
            self.assertEqual((destination / "world" / "world.sav").read_bytes(), b"world")

    def test_copy_verification_failure_preserves_source(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "source"; destination = root / "destination"
            source.mkdir(); destination.mkdir()
            (source / "world.sav").write_bytes(b"world")
            world = WorldSave("world-1", "Meadow", 1, "local", str(source), ("world.sav",), "world.sav", "ready")
            preview = preview_world_operation("backup", world, destination / "copy")
            self.assertTrue(preview.allowed)
            decision = authorize_operation("duplicate", world, SaveSource("local", "local", str(source), True, "ready"), False)
            execute_copy(preview, decision, destination)
            self.assertTrue((source / "world.sav").exists())

    def test_archive_requires_backup_and_explicit_confirmation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "source"; archive = root / "archive"
            source.mkdir(); archive.mkdir(); (source / "world.sav").write_bytes(b"world")
            world = WorldSave("world-1", "Meadow", 1, "local", str(source), ("world.sav",), "world.sav", "ready")
            with self.assertRaises(ValueError):
                archive_world(world, archive, False, "ARCHIVE WORLD")
            target = archive_world(world, archive, True, "ARCHIVE WORLD")
            self.assertEqual((target / "world.sav").read_bytes(), b"world")
            self.assertFalse((source / "world.sav").exists())

    def test_world_package_export_import_and_manifest_validation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "source"; approved = root / "imports"
            source.mkdir(); approved.mkdir()
            (source / "world.sav").write_bytes(b"world")
            world = WorldSave("world-1", "Meadow", 1, "local", str(source), ("world.sav",), "world.sav", "ready")
            archive = root / "meadow.evw"
            export_world(world, archive)
            self.assertEqual(inspect_package(archive)["display_name"], "Meadow")
            imported = import_world(archive, approved / "meadow", approved)
            self.assertEqual(imported["world_id"], "world-1")
            self.assertEqual((approved / "meadow" / "world.sav").read_bytes(), b"world")

    def test_timestamped_backup_creates_recovery_directory(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); source = root / "source"; backups = root / "backups"
            source.mkdir(); backups.mkdir(); (source / "world.sav").write_bytes(b"world")
            world = WorldSave("world-1", "Meadow", 1, "local", str(source), ("world.sav",), "world.sav", "ready")
            destination = create_timestamped_backup(world, backups)
            self.assertTrue(destination.name.startswith("world-1-"))
            self.assertEqual((destination / "world.sav").read_bytes(), b"world")

    def test_backup_requires_profile(self):
        result = plan_backup(ModuleContext("embervault.save-manager", None, "EV-OP-1"), "before test")
        self.assertEqual(result.status, "blocked")

    def test_restore_requires_verified_current_backup(self):
        context = ModuleContext("embervault.save-manager", "default", "EV-OP-2", "approved", "EV-BACKUP-CURRENT")
        self.assertEqual(plan_restore(context, "EV-BACKUP-SOURCE", True).status, "ready")
        self.assertEqual(plan_restore(context, "EV-BACKUP-SOURCE", False).status, "blocked")

    def test_recovery_evidence_is_read_only_and_path_scoped(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("source", "current", "restored"):
                folder = root / name
                folder.mkdir()
                (folder / "save.dat").write_bytes(b"save")
            evidence = build_recovery_evidence("EV-REC-1", root / "source", root / "current", root / "restored", root)
            self.assertTrue(evidence["validated"])
            self.assertFalse(evidence["mutated_files"])
            with self.assertRaises(ValueError):
                build_recovery_evidence("EV-REC-2", root / "source", root / "current", root.parent / "outside", root)

    def test_format_assessment_is_conservative(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            known = root / "world_info.json"
            known.write_text('{"format_version": 1}', encoding="utf-8")
            binary = root / "world.sav"
            binary.write_bytes(b"fixture")
            unknown = root / "unknown.bin"
            unknown.write_bytes(b"fixture")
            self.assertEqual(assess_save_format(known).state, "ready")
            self.assertEqual(assess_save_format(binary).state, "partial")
            self.assertEqual(assess_save_format(unknown).state, "unsupported")


if __name__ == "__main__":
    unittest.main()
