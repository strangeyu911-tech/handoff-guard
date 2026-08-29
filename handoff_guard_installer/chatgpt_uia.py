from __future__ import annotations

import os
import subprocess
import time
import webbrowser
from typing import Any, Iterable

from .errors import SettingsUnavailableError, UnsafeReadError


CHATGPT_TITLE_RE = r"(?i).*chatgpt.*"
SETTINGS_NAMES = ("Settings", "设置")
PERSONALIZATION_NAMES = ("Personalization", "个性化")
CUSTOM_INSTRUCTION_NAMES = (
    "Custom instructions",
    "Custom Instructions",
    "自定义指令",
    "Customize ChatGPT",
    "自定义 ChatGPT",
)
SAVE_NAMES = ("Save", "Done", "保存", "完成")


class ChatGPTUIAAdapter:
    """Conservative Microsoft UI Automation adapter for ChatGPT Desktop.

    It relies on accessible names instead of screen coordinates. When the current
    app build does not expose a unique Custom Instructions editor, reads return
    ``None`` and the installer falls back without writing.
    """

    def __init__(self, desktop: Any | None = None):
        self._desktop = desktop
        self._editor: Any | None = None

    def _uia_desktop(self):
        if self._desktop is not None:
            return self._desktop
        try:
            from pywinauto import Desktop
        except ImportError as exc:
            raise SettingsUnavailableError(
                "Microsoft UI Automation support is not installed; use Copy & Open Settings"
            ) from exc
        self._desktop = Desktop(backend="uia")
        return self._desktop

    def _windows(self) -> list[Any]:
        try:
            return list(self._uia_desktop().windows(title_re=CHATGPT_TITLE_RE, visible_only=True))
        except Exception:
            return []

    def is_chatgpt_available(self) -> bool:
        if self._windows():
            return True
        if os.name != "nt":
            return False
        try:
            os.startfile("chatgpt://")
        except OSError:
            try:
                subprocess.Popen(
                    ["explorer.exe", "chatgpt://"],
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except OSError:
                return False
        for _ in range(24):
            time.sleep(0.25)
            if self._windows():
                return True
        return False

    def _window(self):
        windows = self._windows()
        if not windows:
            raise SettingsUnavailableError("ChatGPT Desktop is not open or could not be found")
        return windows[0]

    @staticmethod
    def _text(control: Any) -> str:
        try:
            return (control.window_text() or "").strip()
        except Exception:
            return ""

    def _find_named(self, root: Any, names: Iterable[str], control_types: tuple[str, ...] = ()) -> list[Any]:
        wanted = tuple(name.casefold() for name in names)
        matches: list[Any] = []
        try:
            controls = root.descendants()
        except Exception:
            return matches
        for control in controls:
            label = self._text(control).casefold()
            if not label or not any(name in label for name in wanted):
                continue
            if control_types:
                try:
                    if control.element_info.control_type not in control_types:
                        continue
                except Exception:
                    continue
            matches.append(control)
        return matches

    def _click_first(self, root: Any, names: Iterable[str]) -> bool:
        for control in self._find_named(root, names, ("Button", "TabItem", "MenuItem", "Text")):
            try:
                control.click_input()
                return True
            except Exception:
                try:
                    control.invoke()
                    return True
                except Exception:
                    continue
        return False

    def _wait_for_named(self, root: Any, names: Iterable[str], timeout: float = 3.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._find_named(root, names):
                return True
            time.sleep(0.2)
        return False

    def _wait_for_editor(self, root: Any, timeout: float = 3.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            editor = self._locate_editor(root)
            if editor is not None:
                return editor
            time.sleep(0.2)
        return None

    def open_personalization(self) -> None:
        window = self._window()
        try:
            window.set_focus()
        except Exception:
            pass
        if self._locate_editor(window) is not None:
            return
        if self._click_first(window, SETTINGS_NAMES):
            self._wait_for_named(window, PERSONALIZATION_NAMES)
        if self._click_first(window, PERSONALIZATION_NAMES):
            self._wait_for_named(window, CUSTOM_INSTRUCTION_NAMES)
        if self._click_first(window, CUSTOM_INSTRUCTION_NAMES):
            self._editor = self._wait_for_editor(window)

    def _locate_editor(self, root: Any | None = None):
        root = root or self._window()
        named_edits = self._find_named(root, CUSTOM_INSTRUCTION_NAMES, ("Edit", "Document"))
        if len(named_edits) == 1:
            return named_edits[0]
        # Some app builds expose the field label separately. Accept a single
        # multiline editor only when the Custom Instructions label is visible.
        if not self._find_named(root, CUSTOM_INSTRUCTION_NAMES):
            return None
        try:
            edits = [
                item
                for item in root.descendants(control_type="Edit")
                if getattr(item.element_info, "is_enabled", True)
            ]
        except Exception:
            return None
        return edits[0] if len(edits) == 1 else None

    def read_custom_instructions(self) -> str | None:
        editor = self._locate_editor()
        if editor is None:
            return None
        self._editor = editor
        try:
            return editor.get_value()
        except Exception:
            try:
                return editor.window_text()
            except Exception:
                return None

    def write_custom_instructions(self, value: str) -> None:
        editor = self._editor or self._locate_editor()
        if editor is None:
            raise UnsafeReadError("Custom Instructions editor is not uniquely accessible; nothing was written")
        try:
            editor.set_edit_text(value)
        except Exception as exc:
            raise UnsafeReadError("UI Automation could not update the editor") from exc
        if not self._click_first(self._window(), SAVE_NAMES):
            raise UnsafeReadError("The Save button was not accessible; verify the preview and use manual fallback")


def open_chatgpt_or_personalization() -> None:
    """Best-effort navigation used only by the manual fallback."""
    if os.name == "nt":
        try:
            subprocess.Popen(
                ["explorer.exe", "chatgpt://settings/personalization"],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return
        except OSError:
            pass
    webbrowser.open("https://chatgpt.com/#settings/Personalization")
