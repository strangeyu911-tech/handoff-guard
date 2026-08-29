from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

from .chatgpt_uia import ChatGPTUIAAdapter, open_chatgpt_or_personalization
from .errors import InstallerError
from .fallback import ManualFallback
from .service import ChangePlan, InstallerService


if os.name == "nt":
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    gdi32 = ctypes.windll.gdi32
else:
    user32 = kernel32 = gdi32 = None


WM_DESTROY = 0x0002
WM_COMMAND = 0x0111
WM_SETFONT = 0x0030
WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000
WS_VSCROLL = 0x00200000
WS_HSCROLL = 0x00100000
WS_BORDER = 0x00800000
ES_MULTILINE = 0x0004
ES_AUTOVSCROLL = 0x0040
ES_AUTOHSCROLL = 0x0080
ES_READONLY = 0x0800
BS_PUSHBUTTON = 0x00000000
SW_SHOW = 5
MB_OK = 0x00000000
MB_ICONINFORMATION = 0x00000040
MB_ICONWARNING = 0x00000030
MB_ICONERROR = 0x00000010
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
COLOR_WINDOW = 5
DEFAULT_GUI_FONT = 17

ID_INSTALL = 101
ID_REPAIR = 102
ID_UNINSTALL = 103
ID_FALLBACK = 104
ID_CONFIRM = 105


LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


_active_window: "InstallerWindow | None" = None


def _message(hwnd, title: str, body: str, flags: int = MB_OK) -> None:
    user32.MessageBoxW(hwnd, body, title, flags)


def _copy_to_clipboard(text: str) -> None:
    encoded = text.encode("utf-16-le") + b"\x00\x00"
    if not user32.OpenClipboard(None):
        raise RuntimeError("Clipboard is currently unavailable")
    handle = None
    try:
        user32.EmptyClipboard()
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
        if not handle:
            raise MemoryError("Could not allocate clipboard memory")
        kernel32.GlobalLock.restype = ctypes.c_void_p
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            raise MemoryError("Could not lock clipboard memory")
        try:
            ctypes.memmove(pointer, encoded, len(encoded))
        finally:
            kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            raise RuntimeError("Could not place the managed block on the clipboard")
        handle = None  # Clipboard now owns the allocation.
    finally:
        if handle:
            kernel32.GlobalFree(handle)
        user32.CloseClipboard()


class InstallerWindow:
    CLASS_NAME = "HandoffGuardInstallerWindow"

    def __init__(self):
        self.service = InstallerService(ChatGPTUIAAdapter())
        self.pending: ChangePlan | None = None
        self.hwnd = None
        self.preview = None
        self.status = None
        self.confirm = None
        self._wndproc = WNDPROC(self._window_proc)

    @staticmethod
    def _create_control(class_name, text, style, x, y, width, height, parent, control_id=0):
        user32.CreateWindowExW.restype = wintypes.HWND
        hwnd = user32.CreateWindowExW(
            0,
            class_name,
            text,
            style,
            x,
            y,
            width,
            height,
            parent,
            ctypes.c_void_p(control_id),
            kernel32.GetModuleHandleW(None),
            None,
        )
        font = gdi32.GetStockObject(DEFAULT_GUI_FONT)
        user32.SendMessageW(hwnd, WM_SETFONT, font, True)
        return hwnd

    def _set_status(self, text: str) -> None:
        user32.SetWindowTextW(self.status, text)

    def _set_preview(self, text: str) -> None:
        user32.SetWindowTextW(self.preview, text.replace("\n", "\r\n"))

    def _prepare(self, operation: str) -> None:
        try:
            self.pending = self.service.prepare(operation)
        except InstallerError as exc:
            self.pending = None
            user32.EnableWindow(self.confirm, False)
            self._set_status(str(exc))
            _message(self.hwnd, "Handoff Guard", str(exc), MB_OK | MB_ICONWARNING)
            return
        self._set_preview(self.pending.preview)
        if self.pending.action == "noop":
            user32.EnableWindow(self.confirm, False)
            self._set_status("Handoff Guard is already up to date; no change is required.")
        else:
            user32.SetWindowTextW(self.confirm, f"Confirm {self.pending.action}")
            user32.EnableWindow(self.confirm, True)
            self._set_status("Review the complete preview. Nothing changes until you confirm.")

    def _apply(self) -> None:
        if self.pending is None:
            return
        try:
            result = self.service.apply(self.pending, self.pending.token)
        except InstallerError as exc:
            self._set_status(str(exc))
            _message(self.hwnd, "Handoff Guard", str(exc), MB_OK | MB_ICONERROR)
            return
        backup = f"\n\nBackup: {result.backup.path}" if result.backup else ""
        self._set_status(f"{result.action.title()} completed and verified.")
        user32.EnableWindow(self.confirm, False)
        _message(
            self.hwnd,
            "Handoff Guard",
            f"The change was saved and verified.{backup}",
            MB_OK | MB_ICONINFORMATION,
        )

    def _fallback(self) -> None:
        try:
            block = ManualFallback(_copy_to_clipboard, open_chatgpt_or_personalization).copy_and_open()
        except Exception as exc:
            _message(self.hwnd, "Handoff Guard", str(exc), MB_OK | MB_ICONERROR)
            return
        self._set_preview(block)
        self._set_status(
            "Managed block copied. Paste it beside existing instructions; do not replace unrelated text."
        )

    def _window_proc(self, hwnd, message, wparam, lparam):
        if message == WM_COMMAND:
            control_id = int(wparam) & 0xFFFF
            if control_id == ID_INSTALL:
                self._prepare("install")
            elif control_id == ID_REPAIR:
                self._prepare("repair")
            elif control_id == ID_UNINSTALL:
                self._prepare("uninstall")
            elif control_id == ID_FALLBACK:
                self._fallback()
            elif control_id == ID_CONFIRM:
                self._apply()
            return 0
        if message == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, message, wparam, lparam)

    def run(self) -> None:
        global _active_window
        _active_window = self
        instance = kernel32.GetModuleHandleW(None)
        window_class = WNDCLASSW()
        window_class.lpfnWndProc = self._wndproc
        window_class.hInstance = instance
        window_class.hCursor = user32.LoadCursorW(None, ctypes.c_void_p(32512))
        window_class.hbrBackground = ctypes.c_void_p(COLOR_WINDOW + 1)
        window_class.lpszClassName = self.CLASS_NAME
        user32.RegisterClassW(ctypes.byref(window_class))
        user32.CreateWindowExW.restype = wintypes.HWND
        self.hwnd = user32.CreateWindowExW(
            0,
            self.CLASS_NAME,
            "Handoff Guard Installer",
            WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            120,
            80,
            900,
            700,
            None,
            None,
            instance,
            None,
        )
        self._create_control("STATIC", "Handoff Guard", WS_CHILD | WS_VISIBLE, 22, 18, 830, 28, self.hwnd)
        self._create_control(
            "STATIC",
            "Model-aware Chat → Work handoffs, routing recommendations, and execution preflight.\n"
            "This installer manages a versioned Custom Instructions block. Existing content is preserved; "
            "nothing is uploaded, and nothing changes before preview confirmation.",
            WS_CHILD | WS_VISIBLE,
            22,
            50,
            835,
            62,
            self.hwnd,
        )
        for label, x, control_id in (
            ("Install / Update", 22, ID_INSTALL),
            ("Repair", 162, ID_REPAIR),
            ("Uninstall", 262, ID_UNINSTALL),
            ("Copy & Open Settings", 372, ID_FALLBACK),
        ):
            self._create_control(
                "BUTTON", label, WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, x, 122, 130 if x != 372 else 180, 32,
                self.hwnd, control_id
            )
        self.preview = self._create_control(
            "EDIT",
            "Choose an action to generate a complete change preview.",
            WS_CHILD | WS_VISIBLE | WS_BORDER | WS_VSCROLL | WS_HSCROLL | ES_MULTILINE | ES_AUTOVSCROLL
            | ES_AUTOHSCROLL | ES_READONLY,
            22,
            170,
            835,
            390,
            self.hwnd,
        )
        self.confirm = self._create_control(
            "BUTTON", "Confirm change", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 697, 575, 160, 34,
            self.hwnd, ID_CONFIRM
        )
        user32.EnableWindow(self.confirm, False)
        self.status = self._create_control(
            "STATIC", "ChatGPT Desktop will be opened automatically when possible.", WS_CHILD | WS_VISIBLE,
            22, 620, 835, 28, self.hwnd
        )
        user32.ShowWindow(self.hwnd, SW_SHOW)
        user32.UpdateWindow(self.hwnd)
        message = MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(message))
            user32.DispatchMessageW(ctypes.byref(message))
        _active_window = None


def main() -> None:
    if os.name != "nt":
        raise SystemExit("Handoff Guard Installer currently supports Windows only")
    InstallerWindow().run()


if __name__ == "__main__":
    main()
