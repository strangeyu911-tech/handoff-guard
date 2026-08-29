from __future__ import annotations

from collections.abc import Callable

from .managed_block import render_managed_block


class ManualFallback:
    def __init__(self, copy: Callable[[str], None], open_settings: Callable[[], None]):
        self.copy = copy
        self.open_settings = open_settings

    def copy_and_open(self) -> str:
        block = render_managed_block()
        self.copy(block)
        self.open_settings()
        return block
