import unittest
from unittest.mock import patch


class Win32ClipboardSignatureTests(unittest.TestCase):
    def test_clipboard_api_uses_pointer_safe_handle_arguments(self):
        from handoff_guard_installer import app_win32

        if app_win32.os.name != "nt":
            self.skipTest("Win32 ctypes declarations are only available on Windows")
        self.assertEqual(app_win32.user32.SetClipboardData.argtypes[1], app_win32.wintypes.HANDLE)
        self.assertEqual(app_win32.kernel32.GlobalLock.argtypes, [app_win32.wintypes.HGLOBAL])
        self.assertEqual(app_win32.kernel32.GlobalAlloc.argtypes[1], app_win32.ctypes.c_size_t)

    @patch("handoff_guard_installer.fallback.render_managed_block")
    def test_manual_fallback_copies_block_before_opening(self, render):
        from handoff_guard_installer.fallback import ManualFallback

        render.return_value = "canonical block"
        copied = []
        opened = []
        result = ManualFallback(copied.append, lambda: opened.append(True)).copy_and_open()
        self.assertEqual(result, "canonical block")
        self.assertEqual(copied, ["canonical block"])
        self.assertEqual(opened, [True])

    @patch("handoff_guard_installer.chatgpt_uia._protocol_is_registered", return_value=False)
    @patch("handoff_guard_installer.chatgpt_uia._launch_discovered_chatgpt", return_value=True)
    def test_unregistered_protocol_uses_discovered_app(self, launch, registered):
        from handoff_guard_installer.chatgpt_uia import open_chatgpt_or_personalization

        with patch("handoff_guard_installer.chatgpt_uia.os.name", "nt"):
            result = open_chatgpt_or_personalization()
        registered.assert_called_once_with("chatgpt")
        launch.assert_called_once_with()
        self.assertIn("ChatGPT was opened", result)
        self.assertIn("Personalization", result)

    @patch("handoff_guard_installer.chatgpt_uia.webbrowser.open", return_value=True)
    @patch("handoff_guard_installer.chatgpt_uia._launch_discovered_chatgpt", return_value=False)
    @patch("handoff_guard_installer.chatgpt_uia._protocol_is_registered", return_value=False)
    def test_app_and_protocol_failure_uses_web_fallback(self, registered, launch, open_web):
        from handoff_guard_installer.chatgpt_uia import open_chatgpt_or_personalization

        with patch("handoff_guard_installer.chatgpt_uia.os.name", "nt"):
            result = open_chatgpt_or_personalization()
        open_web.assert_called_once_with("https://chatgpt.com/")
        self.assertIn("ChatGPT web was opened", result)

    def test_uia_top_level_failure_is_classified_without_content_logging(self):
        from handoff_guard_installer import chatgpt_uia
        from handoff_guard_installer.errors import SettingsUnavailableError

        adapter = chatgpt_uia.ChatGPTUIAAdapter()
        with patch.object(adapter, "_uia_desktop", side_effect=SettingsUnavailableError("backend")):
            with patch.object(chatgpt_uia.LOGGER, "info") as info:
                with self.assertRaises(SettingsUnavailableError):
                    adapter._window()
        messages = " ".join(str(call) for call in info.call_args_list)
        self.assertIn("top_level_window_not_found", messages)
        self.assertNotIn("Custom Instructions", messages)


if __name__ == "__main__":
    unittest.main()
