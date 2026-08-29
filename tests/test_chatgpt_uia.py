import unittest
from unittest.mock import patch

from handoff_guard_installer import chatgpt_uia


class FakeInfo:
    control_type = "Button"
    automation_id = "settings"
    name = "Settings"
    class_name = "Button"
    is_enabled = True
    is_offscreen = False
    process_id = 123


class FakeControl:
    element_info = FakeInfo()

    def __init__(self, children=None, broken=False):
        self._children = children or []
        self.broken = broken
        self.iface_invoke = object()
        self.iface_selection_item = None
        self.iface_legacy_iaccessible = object()
        self.iface_value = None
        self.iface_text = None

    def children(self):
        if self.broken:
            raise RuntimeError("child lookup failed")
        return self._children


class UIADiagnosticTreeTests(unittest.TestCase):
    def test_tree_snapshot_is_bounded_and_isolates_child_errors(self):
        root = FakeControl([FakeControl(broken=True)])
        with patch.object(chatgpt_uia.LOGGER, "info") as info:
            chatgpt_uia._log_uia_tree(root)
        messages = " ".join(str(call) for call in info.call_args_list)
        self.assertIn("stage=uia_tree_node", messages)
        self.assertIn("stage=uia_tree_children", messages)
        self.assertNotIn("child lookup failed", messages)

    def test_sensitive_editor_name_is_redacted(self):
        self.assertEqual(
            chatgpt_uia._safe_tree_name(None, "Edit", "existing user instructions"),
            "<redacted len=26>",
        )


if __name__ == "__main__":
    unittest.main()
