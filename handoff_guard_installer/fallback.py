from __future__ import annotations

from collections.abc import Callable
import webbrowser

from .managed_block import render_managed_block


class GuidedInstall:
    """Copy a generated block and open the supported ChatGPT web entry point."""

    def __init__(self, copy: Callable[[str], None], open_web: Callable[[], None]):
        self.copy = copy
        self.open_web = open_web

    def copy_block(self) -> str:
        block = render_managed_block()
        self.copy(block)
        return block

    def copy_and_open(self) -> str:
        """Compatibility helper for older callers; it still performs no account write."""
        block = self.copy_block()
        self.open_web()
        return block


ManualFallback = GuidedInstall


def open_chatgpt_web() -> str:
    """Open only the public ChatGPT web URL; no desktop deep link is used."""
    target = "https://chatgpt.com/"
    try:
        opened = webbrowser.open(target)
    except Exception:
        opened = False
    if opened:
        return (
            "ChatGPT Web opened. There is currently no supported settings deep link. "
            "Open Settings → Personalization → Custom Instructions manually."
        )
    return (
        "Open https://chatgpt.com/ manually, then go to Settings → Personalization → "
        "Custom Instructions."
    )
