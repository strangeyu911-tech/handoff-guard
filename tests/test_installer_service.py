import tempfile
import unittest
from pathlib import Path

from handoff_guard_installer.backup import LocalBackupStore
from handoff_guard_installer.errors import (
    ConfirmationRequiredError,
    SettingsUnavailableError,
    UnsafeReadError,
    VerificationError,
)
from handoff_guard_installer.fallback import ManualFallback
from handoff_guard_installer.managed_block import END_MARKER, inspect_managed_block, render_managed_block
from handoff_guard_installer.service import InstallerService


class FakeAdapter:
    def __init__(self, value="", available=True, readable=True, persist_writes=True, raise_on_write=False):
        self.value = value
        self.available = available
        self.readable = readable
        self.persist_writes = persist_writes
        self.raise_on_write = raise_on_write
        self.opened = 0
        self.writes = []

    def is_chatgpt_available(self):
        return self.available

    def open_personalization(self):
        self.opened += 1

    def read_custom_instructions(self):
        return self.value if self.readable else None

    def write_custom_instructions(self, value):
        self.writes.append(value)
        if self.raise_on_write:
            raise RuntimeError("simulated UI failure")
        if self.persist_writes:
            self.value = value


class InstallerServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.backups = LocalBackupStore(Path(self.temp.name))

    def test_preview_is_required_before_write(self):
        adapter = FakeAdapter("mine")
        service = InstallerService(adapter, self.backups)
        plan = service.prepare("install")
        self.assertEqual(adapter.writes, [])
        with self.assertRaises(ConfirmationRequiredError):
            service.apply(plan, "wrong-token")
        self.assertEqual(adapter.writes, [])

    def test_confirmed_install_creates_local_backup_and_verifies(self):
        adapter = FakeAdapter("mine")
        service = InstallerService(adapter, self.backups)
        plan = service.prepare("install")
        result = service.apply(plan, plan.token)
        self.assertTrue(result.verified)
        self.assertTrue(result.backup.path.is_file())
        self.assertEqual(inspect_managed_block(adapter.value).status, "installed")

    def test_unreadable_settings_never_write(self):
        adapter = FakeAdapter(readable=False)
        service = InstallerService(adapter, self.backups)
        with self.assertRaises(UnsafeReadError):
            service.prepare("install")
        self.assertEqual(adapter.writes, [])

    def test_missing_chatgpt_is_reported_clearly(self):
        adapter = FakeAdapter(available=False)
        with self.assertRaises(SettingsUnavailableError):
            InstallerService(adapter, self.backups).prepare("install")

    def test_changed_value_after_preview_is_not_overwritten(self):
        adapter = FakeAdapter("first")
        service = InstallerService(adapter, self.backups)
        plan = service.prepare("install")
        adapter.value = "user changed this"
        with self.assertRaises(VerificationError):
            service.apply(plan, plan.token)
        self.assertEqual(adapter.writes, [])

    def test_write_verification_failure_keeps_backup(self):
        adapter = FakeAdapter("mine", persist_writes=False)
        service = InstallerService(adapter, self.backups)
        plan = service.prepare("install")
        with self.assertRaises(VerificationError):
            service.apply(plan, plan.token)
        self.assertEqual(len(list(Path(self.temp.name).glob("*.json"))), 1)

    def test_ui_write_failure_reports_recoverable_backup(self):
        adapter = FakeAdapter("mine", raise_on_write=True)
        service = InstallerService(adapter, self.backups)
        plan = service.prepare("install")
        with self.assertRaisesRegex(VerificationError, "Restore from backup"):
            service.apply(plan, plan.token)
        self.assertEqual(len(list(Path(self.temp.name).glob("*.json"))), 1)

    def test_repair_replaces_a_truncated_block_after_preview(self):
        adapter = FakeAdapter(render_managed_block().replace(END_MARKER, ""))
        service = InstallerService(adapter, self.backups)
        plan = service.prepare("repair")
        self.assertEqual(plan.action, "repair")
        result = service.apply(plan, plan.token)
        self.assertTrue(result.verified)
        self.assertEqual(inspect_managed_block(adapter.value).status, "installed")

    def test_manual_fallback_copies_and_opens_without_automatic_write(self):
        copied = []
        opened = []
        block = ManualFallback(copied.append, lambda: opened.append(True)).copy_and_open()
        self.assertEqual(copied, [block])
        self.assertEqual(opened, [True])
        self.assertEqual(inspect_managed_block(block).status, "installed")


if __name__ == "__main__":
    unittest.main()
