from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

from .errors import InstallerError
from .fallback import open_chatgpt_web
from .managed_block import render_managed_block
from .service import ChangePlan, InstallerService


if os.name == "nt":
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    gdi32 = ctypes.windll.gdi32

    # ctypes defaults unspecified parameters to C ``int``.  That is unsafe
    # for HWND/HANDLE values on 64-bit Windows: a valid handle can exceed the
    # signed 32-bit range and fail before the Win32 API is called.  Declare
    # every handle-bearing function used by the installer explicitly.
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
    user32.MessageBoxW.restype = ctypes.c_int
    user32.CreateWindowExW.argtypes = [
        wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.HWND, ctypes.c_void_p, wintypes.HINSTANCE, ctypes.c_void_p,
    ]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.SetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
    user32.SetWindowTextW.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.EnableWindow.argtypes = [wintypes.HWND, wintypes.BOOL]
    user32.EnableWindow.restype = wintypes.BOOL
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = ctypes.c_ssize_t
    user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.DefWindowProcW.restype = ctypes.c_ssize_t
    user32.PostQuitMessage.argtypes = [ctypes.c_int]
    user32.PostQuitMessage.restype = None
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL
    user32.UpdateWindow.argtypes = [wintypes.HWND]
    user32.UpdateWindow.restype = wintypes.BOOL
    user32.LoadCursorW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
    user32.LoadCursorW.restype = wintypes.HANDLE
    user32.RegisterClassW.restype = ctypes.c_ushort
    user32.GetMessageW.restype = wintypes.BOOL
    user32.TranslateMessage.restype = wintypes.BOOL
    user32.DispatchMessageW.restype = ctypes.c_ssize_t

    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wintypes.HMODULE
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL
    gdi32.GetStockObject.argtypes = [ctypes.c_int]
    gdi32.GetStockObject.restype = wintypes.HGDIOBJ
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

ID_GENERATE = 101
ID_UPDATE = 102
ID_REMOVE = 103
ID_REPAIR = 104
ID_COPY_BLOCK = 105
ID_OPEN_WEB = 106
ID_CONFIRM = 107


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


if os.name == "nt":
    user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
    user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
    user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
    user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]


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
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
        if not handle:
            raise MemoryError("Could not allocate clipboard memory")
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
        self.service = InstallerService()
        self.pending: ChangePlan | None = None
        self.hwnd = None
        self.source = None
        self.preview = None
        self.status = None
        self.confirm = None
        self._wndproc = WNDPROC(self._window_proc)

    @staticmethod
    def _create_control(class_name, text, style, x, y, width, height, parent, control_id=0):
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

    @staticmethod
    def _get_text(control) -> str:
        length = user32.GetWindowTextLengthW(control)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(control, buffer, length + 1)
        return buffer.value

    def _prepare(self, operation: str) -> None:
        try:
            self.pending = self.service.prepare(operation, self._get_text(self.source))
        except InstallerError as exc:
            self.pending = None
            user32.EnableWindow(self.confirm, False)
            self._set_status(str(exc))
            _message(self.hwnd, "Handoff Guard", str(exc), MB_OK | MB_ICONWARNING)
            return
        self._set_preview(self.pending.preview)
        if self.pending.action == "noop":
            user32.EnableWindow(self.confirm, False)
            self._set_status("The supplied text already contains the current Handoff Guard block.")
        else:
            user32.SetWindowTextW(self.confirm, "Copy generated instructions")
            user32.EnableWindow(self.confirm, True)
            self._set_status("Review the local preview. ChatGPT will not be changed by this installer.")

    def _generate(self) -> None:
        self._set_preview(render_managed_block())
        self.pending = None
        user32.EnableWindow(self.confirm, False)
        self._set_status("Managed block generated locally. Use Copy managed block, then save it in ChatGPT yourself.")

    def _copy_block(self) -> None:
        try:
            _copy_to_clipboard(render_managed_block())
        except Exception as exc:
            _message(self.hwnd, "Handoff Guard", str(exc), MB_OK | MB_ICONERROR)
            return
        self._set_preview(render_managed_block())
        self._set_status("Handoff Guard block copied. No ChatGPT account setting was changed.")

    def _open_web(self) -> None:
        self._set_status(open_chatgpt_web())

    def _apply(self) -> None:
        if self.pending is None:
            return
        try:
            result = self.service.apply(self.pending, self.pending.token)
        except InstallerError as exc:
            self._set_status(str(exc))
            _message(self.hwnd, "Handoff Guard", str(exc), MB_OK | MB_ICONERROR)
            return
        try:
            _copy_to_clipboard(result.output)
        except Exception as exc:
            self._set_status(str(exc))
            _message(self.hwnd, "Handoff Guard", str(exc), MB_OK | MB_ICONERROR)
            return
        self._set_preview(result.output)
        self._set_status(
            "Generated instructions copied. No ChatGPT account setting was changed; manually review and save them."
        )
        user32.EnableWindow(self.confirm, False)
        _message(
            self.hwnd,
            "Handoff Guard",
            "The local instructions were generated and copied.\n\n"
            "Now open ChatGPT Web, go to Settings → Personalization → Custom Instructions, "
            "preserve unrelated content, and save manually.",
            MB_OK | MB_ICONINFORMATION,
        )

    def _window_proc(self, hwnd, message, wparam, lparam):
        if message == WM_COMMAND:
            control_id = int(wparam) & 0xFFFF
            if control_id == ID_GENERATE:
                self._generate()
            elif control_id == ID_UPDATE:
                self._prepare("update")
            elif control_id == ID_REMOVE:
                self._prepare("uninstall")
            elif control_id == ID_REPAIR:
                self._prepare("repair")
            elif control_id == ID_COPY_BLOCK:
                self._copy_block()
            elif control_id == ID_OPEN_WEB:
                self._open_web()
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
        self.hwnd = user32.CreateWindowExW(
            0,
            self.CLASS_NAME,
            "Handoff Guard Installer",
            WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            120,
            80,
            900,
            820,
            None,
            None,
            instance,
            None,
        )
        self._create_control("STATIC", "Handoff Guard", WS_CHILD | WS_VISIBLE, 22, 18, 830, 28, self.hwnd)
        self._create_control(
            "STATIC",
            "Guided Install for the Handoff Guard managed block.\n"
            "This installer only generates, validates, and copies local text. It never reads or changes your ChatGPT account.",
            WS_CHILD | WS_VISIBLE,
            22,
            50,
            835,
            62,
            self.hwnd,
        )
        self._create_control(
            "STATIC",
            "Optional: paste your current Custom Instructions here to create a local update or removal result. "
            "Text stays on this device.",
            WS_CHILD | WS_VISIBLE,
            22,
            116,
            835,
            28,
            self.hwnd,
        )
        self.source = self._create_control(
            "EDIT",
            "",
            WS_CHILD | WS_VISIBLE | WS_BORDER | WS_VSCROLL | WS_HSCROLL | ES_MULTILINE | ES_AUTOVSCROLL
            | ES_AUTOHSCROLL,
            22,
            145,
            835,
            165,
            self.hwnd,
        )
        for label, x, width, control_id in (
            ("Generate block", 22, 125, ID_GENERATE),
            ("Update instructions", 157, 145, ID_UPDATE),
            ("Removal instructions", 312, 150, ID_REMOVE),
            ("Repair instructions", 472, 145, ID_REPAIR),
            ("Copy managed block", 627, 145, ID_COPY_BLOCK),
        ):
            self._create_control(
                "BUTTON", label, WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, x, 320, width, 32,
                self.hwnd, control_id
            )
        self._create_control(
            "BUTTON", "Open ChatGPT Web", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 22, 365, 160, 32,
            self.hwnd, ID_OPEN_WEB
        )
        self._create_control(
            "STATIC",
            "Local result / preview (no account verification):",
            WS_CHILD | WS_VISIBLE,
            22,
            408,
            835,
            24,
            self.hwnd,
        )
        self.preview = self._create_control(
            "EDIT",
            "Choose an action to generate a complete change preview.",
            WS_CHILD | WS_VISIBLE | WS_BORDER | WS_VSCROLL | WS_HSCROLL | ES_MULTILINE | ES_AUTOVSCROLL
            | ES_AUTOHSCROLL | ES_READONLY,
            22,
            435,
            835,
            265,
            self.hwnd,
        )
        self.confirm = self._create_control(
            "BUTTON", "Copy generated instructions", WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 657, 710, 200, 34,
            self.hwnd, ID_CONFIRM
        )
        user32.EnableWindow(self.confirm, False)
        self.status = self._create_control(
            "STATIC",
            "Next: Open ChatGPT Web → Settings → Personalization → Custom Instructions. "
            "Preserve unrelated content and save manually.",
            WS_CHILD | WS_VISIBLE,
            22,
            760,
            835,
            28,
            self.hwnd,
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
