import tempfile
import unittest
from pathlib import Path

from handoff_guard_installer.backup import LocalBackupStore
from handoff_guard_installer.errors import ConfirmationRequiredError, RepairRequiredError
from handoff_guard_installer.fallback import GuidedInstall
from handoff_guard_installer.managed_block import END_MARKER, inspect_managed_block, render_managed_block
from handoff_guard_installer.service import InstallerService


class InstallerServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.backups = LocalBackupStore(Path(self.temp.name))
        self.service = InstallerService(self.backups)

    def test_preview_is_required_before_local_copy(self):
        plan = self.service.prepare("install", "mine")
        with self.assertRaises(ConfirmationRequiredError):
            self.service.apply(plan, "wrong-token")

    def test_confirmed_install_is_local_and_validated(self):
        plan = self.service.prepare("install", "mine")
        result = self.service.apply(plan, plan.token)
        self.assertTrue(result.validated)
        self.assertIsNone(result.backup)
        self.assertEqual(result.output, plan.after)
        self.assertEqual(inspect_managed_block(result.output).status, "installed")

    def test_update_preserves_user_content_and_replaces_old_block(self):
        before = f"Keep this.\n\n{render_managed_block('old policy', '0.0.1')}\n\nKeep that."
        plan = self.service.prepare("update", before)
        result = self.service.apply(plan, plan.token)
        self.assertEqual(result.action, "update")
        self.assertTrue(result.output.startswith("Keep this."))
        self.assertTrue(result.output.endswith("Keep that."))
        self.assertNotIn("old policy", result.output)

    def test_removal_is_local_and_only_removes_managed_block(self):
        before = "Keep this.\n\n" + render_managed_block() + "\n\nKeep that."
        plan = self.service.prepare("uninstall", before)
        result = self.service.apply(plan, plan.token)
        self.assertEqual(result.output, "Keep this.\n\nKeep that.")

    def test_repair_regenerates_a_truncated_block(self):
        broken = render_managed_block().replace(END_MARKER, "")
        plan = self.service.prepare("repair", broken)
        result = self.service.apply(plan, plan.token)
        self.assertEqual(result.action, "repair")
        self.assertEqual(inspect_managed_block(result.output).status, "installed")

    def test_update_of_corrupt_block_requires_repair(self):
        broken = render_managed_block().replace(END_MARKER, "")
        with self.assertRaises(RepairRequiredError):
            self.service.prepare("update", broken)

    def test_explicit_local_backup_only_contains_user_provided_text(self):
        record = self.service.backup_text("mine", "user-provided")
        self.assertTrue(record.path.is_file())
        self.assertEqual(len(list(Path(self.temp.name).glob("*.json"))), 1)

    def test_guided_install_copies_without_opening_or_writing_an_account(self):
        copied = []
        opened = []
        guided = GuidedInstall(copied.append, lambda: opened.append(True))
        block = guided.copy_block()
        self.assertEqual(copied, [block])
        self.assertEqual(opened, [])
        self.assertEqual(inspect_managed_block(block).status, "installed")


if __name__ == "__main__":
    unittest.main()
