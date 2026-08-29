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
    def test_guided_install_copies_block_without_opening(self, render):
        from handoff_guard_installer.fallback import GuidedInstall

        render.return_value = "canonical block"
        copied = []
        opened = []
        result = GuidedInstall(copied.append, lambda: opened.append(True)).copy_block()
        self.assertEqual(result, "canonical block")
        self.assertEqual(copied, ["canonical block"])
        self.assertEqual(opened, [])

    @patch("handoff_guard_installer.fallback.webbrowser.open", return_value=True)
    def test_open_web_uses_only_public_chatgpt_url(self, open_web):
        from handoff_guard_installer.fallback import open_chatgpt_web

        result = open_chatgpt_web()
        open_web.assert_called_once_with("https://chatgpt.com/")
        self.assertIn("ChatGPT Web opened", result)
        self.assertIn("no supported settings deep link", result)


if __name__ == "__main__":
    unittest.main()
