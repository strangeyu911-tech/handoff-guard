from __future__ import annotations

import os
import logging
import subprocess
import time
import webbrowser
from pathlib import Path
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
LOGGER = logging.getLogger("handoff_guard.uia")
UIA_TREE_MAX_NODES = 300
UIA_TREE_MAX_DEPTH = 10
UIA_SENSITIVE_CONTROL_TYPES = {"Edit", "Document"}


def _configure_logging() -> None:
    if LOGGER.handlers:
        return
    try:
        log_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "HandoffGuard"
        log_dir.mkdir(parents=True, exist_ok=True)
        target = log_dir / "installer-uia.log"
    except OSError:
        target = Path(os.environ.get("TEMP", ".")) / "handoff-guard-uia.log"
    try:
        handler = logging.FileHandler(target, encoding="utf-8")
    except OSError:
        # Diagnostics must never turn a safe read failure into an installer
        # failure (for example when a previous process still holds the log).
        LOGGER.addHandler(logging.NullHandler())
        return
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False


def _control_metadata(control: Any) -> str:
    try:
        info = control.element_info
        values = {
            "control_type": getattr(info, "control_type", None),
            "automation_id": getattr(info, "automation_id", None),
            "name": getattr(info, "name", None),
            "process_id": getattr(info, "process_id", None),
            "value_pattern": hasattr(control, "iface_value"),
            "text_pattern": hasattr(control, "iface_text"),
        }
        return ", ".join(f"{key}={value!r}" for key, value in values.items())
    except Exception as exc:
        return f"metadata_error={type(exc).__name__}"


def _safe_control_field(control: Any, field: str) -> tuple[Any, str | None]:
    try:
        info = control.element_info
        return getattr(info, field), None
    except Exception as exc:
        return None, type(exc).__name__


def _safe_pattern(control: Any, pattern: str) -> str:
    try:
        return "available" if getattr(control, pattern) is not None else "absent"
    except Exception as exc:
        return f"error:{type(exc).__name__}"


def _safe_tree_name(control: Any, control_type: Any, name: Any) -> str:
    if not name:
        return ""
    name = str(name)
    if control_type in UIA_SENSITIVE_CONTROL_TYPES:
        return f"<redacted len={len(name)}>"
    if len(name) > 160:
        return f"<redacted len={len(name)}>"
    return name


def _tree_node_line(control: Any, depth: int, path: str) -> str:
    fields: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for field in ("control_type", "automation_id", "name", "class_name", "is_enabled", "is_offscreen", "process_id"):
        value, error = _safe_control_field(control, field)
        fields[field] = value
        if error:
            errors[field] = error
    fields["name"] = _safe_tree_name(control, fields["control_type"], fields["name"])
    patterns = {
        "invoke": _safe_pattern(control, "iface_invoke"),
        "selection_item": _safe_pattern(control, "iface_selection_item"),
        "legacy_iaccessible": _safe_pattern(control, "iface_legacy_iaccessible"),
        "value": _safe_pattern(control, "iface_value"),
        "text": _safe_pattern(control, "iface_text"),
    }
    return (
        f"stage=uia_tree_node depth={depth} path={path} "
        f"control_type={fields['control_type']!r} automation_id={fields['automation_id']!r} "
        f"name={fields['name']!r} class_name={fields['class_name']!r} "
        f"is_enabled={fields['is_enabled']!r} is_offscreen={fields['is_offscreen']!r} "
        f"process_id={fields['process_id']!r} patterns={patterns!r} metadata_errors={errors!r}"
    )


def _log_uia_tree(root: Any) -> None:
    """Log a bounded, content-safe UIA tree snapshot for selector diagnosis."""
    _configure_logging()
    count = 0
    stack: list[tuple[Any, int, str]] = [(root, 0, "0")]
    while stack and count < UIA_TREE_MAX_NODES:
        control, depth, path = stack.pop()
        try:
            LOGGER.info(_tree_node_line(control, depth, path))
        except Exception as exc:
            LOGGER.info("stage=uia_tree_node depth=%d path=%s metadata_error=%s", depth, path, type(exc).__name__)
        count += 1
        if depth >= UIA_TREE_MAX_DEPTH:
            continue
        try:
            children = list(control.children())
        except Exception as exc:
            LOGGER.info("stage=uia_tree_children depth=%d path=%s error=%s", depth, path, type(exc).__name__)
            continue
        for index, child in reversed(list(enumerate(children))):
            stack.append((child, depth + 1, f"{path}.{index}"))
    if stack:
        LOGGER.info(
            "stage=uia_tree_truncated nodes=%d max_nodes=%d max_depth=%d remaining=%d",
            count,
            UIA_TREE_MAX_NODES,
            UIA_TREE_MAX_DEPTH,
            len(stack),
        )
    else:
        LOGGER.info("stage=uia_tree_complete nodes=%d max_nodes=%d max_depth=%d", count, UIA_TREE_MAX_NODES, UIA_TREE_MAX_DEPTH)


def _log_control(stage: str, control: Any, message: str) -> None:
    _configure_logging()
    LOGGER.info("stage=%s %s %s", stage, message, _control_metadata(control))


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
            _configure_logging()
            LOGGER.exception("stage=uia_backend_initialization failed: pywinauto import")
            raise SettingsUnavailableError(
                "Microsoft UI Automation support is not installed; use Copy & Open Settings"
            ) from exc
        try:
            self._desktop = Desktop(backend="uia")
        except Exception as exc:
            _configure_logging()
            LOGGER.exception("stage=uia_backend_initialization failed: %s", type(exc).__name__)
            raise SettingsUnavailableError("Microsoft UI Automation backend could not be initialized") from exc
        return self._desktop

    def _windows(self) -> list[Any]:
        try:
            return list(self._uia_desktop().windows(title_re=CHATGPT_TITLE_RE, visible_only=True))
        except SettingsUnavailableError:
            return []
        except Exception as exc:
            _configure_logging()
            LOGGER.exception("stage=top_level_window_lookup unexpected=%s", type(exc).__name__)
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
            _configure_logging()
            LOGGER.info("stage=top_level_window_not_found")
            raise SettingsUnavailableError("ChatGPT Desktop is not open or could not be found")
        _log_control("top_level_window_found", windows[0], "window_selected")
        _log_uia_tree(windows[0])
        return windows[0]

    @staticmethod
    def _text(control: Any) -> str:
        try:
            value = (control.window_text() or "").strip()
            if value:
                return value
        except Exception:
            pass
        try:
            return (getattr(control.element_info, "name", "") or "").strip()
        except Exception:
            return ""

    def _find_named(self, root: Any, names: Iterable[str], control_types: tuple[str, ...] = ()) -> list[Any]:
        wanted = tuple(name.casefold() for name in names)
        matches: list[Any] = []
        try:
            controls = root.descendants()
        except Exception as exc:
            _configure_logging()
            LOGGER.exception("stage=control_tree_lookup unexpected=%s", type(exc).__name__)
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
        settings_clicked = self._click_first(window, SETTINGS_NAMES)
        if settings_clicked:
            if not self._wait_for_named(window, PERSONALIZATION_NAMES):
                _configure_logging()
                LOGGER.info("stage=settings_surface_not_found reason=personalization_not_visible")
        else:
            _configure_logging()
            LOGGER.info("stage=settings_surface_not_found")
        if self._click_first(window, PERSONALIZATION_NAMES):
            self._wait_for_named(window, CUSTOM_INSTRUCTION_NAMES)
        else:
            _configure_logging()
            LOGGER.info("stage=personalization_control_not_found")
        if self._click_first(window, CUSTOM_INSTRUCTION_NAMES):
            self._editor = self._wait_for_editor(window)
        else:
            _configure_logging()
            LOGGER.info("stage=custom_instructions_control_not_found")

    def _locate_editor(self, root: Any | None = None):
        root = root or self._window()
        named_edits = self._find_named(root, CUSTOM_INSTRUCTION_NAMES, ("Edit", "Document"))
        if len(named_edits) == 1:
            _log_control("custom_instructions_control_found", named_edits[0], "named_editor")
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
        except Exception as exc:
            _configure_logging()
            LOGGER.exception("stage=custom_instructions_control_lookup unexpected=%s", type(exc).__name__)
            return None
        if len(edits) == 1:
            _log_control("custom_instructions_control_found", edits[0], "label_scoped_editor")
            return edits[0]
        _configure_logging()
        LOGGER.info("stage=custom_instructions_control_not_found reason=editor_count_%d", len(edits))
        return None

    def read_custom_instructions(self) -> str | None:
        editor = self._locate_editor()
        if editor is None:
            return None
        self._editor = editor
        try:
            return editor.get_value()
        except Exception as value_exc:
            _log_control("value_pattern_unavailable", editor, f"get_value_failed={type(value_exc).__name__}")
            try:
                value = editor.window_text()
                if not value:
                    _log_control("value_returned_empty", editor, "window_text_empty")
                return value
            except Exception as text_exc:
                _log_control("value_pattern_unavailable", editor, f"window_text_failed={type(text_exc).__name__}")
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


def open_chatgpt_or_personalization() -> str:
    """Open ChatGPT without showing a Windows unregistered-protocol dialog."""
    guidance = "Open Settings → Personalization → Custom Instructions."
    if os.name == "nt":
        if _protocol_is_registered("chatgpt"):
            try:
                os.startfile("chatgpt://settings/personalization")
                return "ChatGPT Settings was opened. " + guidance
            except OSError:
                pass
        if _launch_discovered_chatgpt():
            return "ChatGPT was opened. " + guidance
    try:
        if webbrowser.open("https://chatgpt.com/"):
            return "ChatGPT web was opened. " + guidance
    except Exception:
        pass
    return "Open ChatGPT manually, then " + guidance


def _protocol_is_registered(protocol: str) -> bool:
    if os.name != "nt":
        return False
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, protocol) as key:
            with winreg.OpenKey(key, r"shell\open\command") as command_key:
                command = winreg.QueryValue(command_key, None)
                return bool(command and command.strip())
    except OSError:
        return False


def _launch_discovered_chatgpt() -> bool:
    if os.name != "nt":
        return False
    roots = (
        Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
        Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
    )
    for root in roots:
        if not root.is_dir():
            continue
        try:
            candidates = sorted(
                path for path in root.rglob("*.lnk")
                if "chatgpt" in path.stem.casefold() and "uninstall" not in path.stem.casefold()
            )
        except OSError:
            continue
        for shortcut in candidates:
            try:
                os.startfile(str(shortcut))
                return True
            except OSError:
                continue
    return False
