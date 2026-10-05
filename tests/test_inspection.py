import tempfile
import unittest
from pathlib import Path

from embervault_sdk import ModuleContext
from src.inspection import inspect_save_root


class SaveInspectionTests(unittest.TestCase):
    def test_inspection_is_deterministic_and_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "world").mkdir()
            (root / "world" / "save.dat").write_bytes(b"save-data")
            context = ModuleContext("embervault.save-manager", "research", "EV-INSPECT-1")
            first = inspect_save_root(context, root)
            second = inspect_save_root(context, root)
            self.assertEqual(first, second)
            self.assertEqual(first["state"], "ready")
            self.assertFalse(first["mutated_files"])
            self.assertEqual(first["files"][0]["relative_path"], "world/save.dat")

    def test_missing_expected_file_is_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            result = inspect_save_root(ModuleContext("embervault.save-manager", "default", "EV-INSPECT-2"),
                                       Path(directory), expected_files=["world/save.dat"])
            self.assertEqual(result["state"], "partial")
            self.assertEqual(result["missing_files"], ["world/save.dat"])

    def test_wrong_context_and_missing_root_are_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(inspect_save_root(ModuleContext("other", "default", "EV-1"), root)["state"], "blocked")
            self.assertEqual(inspect_save_root(ModuleContext("embervault.save-manager", "default", "EV-2"), root / "missing")["state"], "blocked")


if __name__ == "__main__":
    unittest.main()
