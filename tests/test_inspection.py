import tempfile
import unittest
from pathlib import Path

from src.inspection import inspect_save_root, is_within_root


class SaveInspectionTests(unittest.TestCase):
    def test_inspection_is_deterministic_and_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "world").mkdir()
            (root / "world" / "save.dat").write_bytes(b"save-data")
            first = inspect_save_root(root).to_dict()
            second = inspect_save_root(root).to_dict()
            self.assertEqual(first, second)
            self.assertEqual(first["state"], "ready")
            self.assertEqual(first["files"][0]["relative_path"], "world/save.dat")

    def test_missing_expected_file_is_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            result = inspect_save_root(Path(directory), expected_paths=["world/save.dat"]).to_dict()
            self.assertEqual(result["state"], "partial")
            self.assertEqual(result["files"][-1]["relative_path"], "world/save.dat")

    def test_wrong_context_and_missing_root_are_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertFalse(is_within_root(root / "outside", root / "nested"))
            self.assertEqual(inspect_save_root(root / "missing").state, "blocked")


if __name__ == "__main__":
    unittest.main()
