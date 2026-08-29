import sys

from handoff_guard_installer.app_win32 import main


def _packaged_smoke() -> None:
    """Import the packaged installer without accessing ChatGPT or its account."""
    import handoff_guard_installer.app_win32  # noqa: F401


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        _packaged_smoke()
    else:
        main()
