import sys

from handoff_guard_installer.app_win32 import main
from handoff_guard_installer.chatgpt_uia import ChatGPTUIAAdapter


def _packaged_smoke() -> None:
    """Import and initialize the packaged UIA runtime without changing settings."""
    adapter = ChatGPTUIAAdapter()
    adapter._uia_desktop()


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        _packaged_smoke()
    else:
        main()
