import unittest

from handoff_guard_installer.errors import RepairRequiredError
from handoff_guard_installer.managed_block import (
    END_MARKER,
    canonical_payload,
    inspect_managed_block,
    install_or_update,
    render_managed_block,
    uninstall,
)


class ManagedBlockTests(unittest.TestCase):
    def test_empty_custom_instructions_install(self):
        updated, action = install_or_update("")
        self.assertEqual(action, "install")
        self.assertEqual(inspect_managed_block(updated).status, "installed")

    def test_existing_user_content_is_preserved(self):
        original = "Always answer me in Chinese."
        updated, _ = install_or_update(original)
        self.assertTrue(updated.startswith(original))
        self.assertIn(canonical_payload(), updated)

    def test_same_version_and_payload_do_not_duplicate(self):
        installed = render_managed_block()
        updated, action = install_or_update(installed)
        self.assertEqual(action, "noop")
        self.assertEqual(updated.count("HANDOFF-GUARD:BEGIN"), 1)

    def test_old_version_is_updated_in_place(self):
        before = f"prefix\n\n{render_managed_block('old policy', '0.0.1')}\n\nsuffix"
        updated, action = install_or_update(before)
        self.assertEqual(action, "update")
        self.assertTrue(updated.startswith("prefix"))
        self.assertTrue(updated.endswith("suffix"))
        self.assertNotIn("old policy", updated)

    def test_uninstall_removes_only_managed_region(self):
        before, _ = install_or_update("user-before\nuser-after")
        updated, action = uninstall(before)
        self.assertEqual(action, "uninstall")
        self.assertEqual(updated, "user-before\nuser-after")

    def test_truncated_block_requires_repair(self):
        broken = render_managed_block().replace(END_MARKER, "")
        self.assertEqual(inspect_managed_block(broken).status, "corrupt")
        with self.assertRaises(RepairRequiredError):
            install_or_update(broken)

    def test_modified_payload_fails_checksum(self):
        broken = render_managed_block().replace("使用 Handoff Guard", "使用 Different Guard")
        state = inspect_managed_block(broken)
        self.assertEqual(state.status, "corrupt")
        self.assertIn("checksum", state.reason)

    def test_duplicate_blocks_require_repair(self):
        duplicated = f"{render_managed_block()}\n{render_managed_block()}"
        self.assertEqual(inspect_managed_block(duplicated).status, "corrupt")


if __name__ == "__main__":
    unittest.main()
