import unittest

from embervault_sdk import ModuleContext
from src.module import plan_backup, plan_restore


class SaveManagerTests(unittest.TestCase):
    def test_backup_requires_profile(self):
        result = plan_backup(ModuleContext("embervault.save-manager", None, "EV-OP-1"), "before test")
        self.assertEqual(result.status, "blocked")

    def test_restore_requires_verified_current_backup(self):
        context = ModuleContext("embervault.save-manager", "default", "EV-OP-2", "approved", "EV-BACKUP-CURRENT")
        self.assertEqual(plan_restore(context, "EV-BACKUP-SOURCE", True).status, "ready")
        self.assertEqual(plan_restore(context, "EV-BACKUP-SOURCE", False).status, "blocked")


if __name__ == "__main__":
    unittest.main()
