#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runtime" / "custom-instructions.txt"
TARGET = ROOT / "CUSTOM-INSTRUCTIONS.md"


def render(payload: str) -> str:
    return f"""# Handoff Guard — Manual ChatGPT installation

This is a generated manual-installation artifact for the ChatGPT runtime adapter. Handoff Guard Core—not this document—is the product's canonical behavior layer. The Windows installer and this page both consume `runtime/custom-instructions.txt`, so there is no separate installer policy.

Paste only the following block into ChatGPT Settings → Personalization → Custom Instructions. Preserve any unrelated instructions already present.

```text
{payload.strip()}
```

The runtime adapter is advisory: it cannot switch models, inspect provider APIs, or execute repository scripts. Use the Windows installer for managed install, update, repair, backup, and uninstall behavior.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the manual ChatGPT installation document")
    parser.add_argument("--check", action="store_true", help="fail if the generated document is stale")
    args = parser.parse_args()
    expected = render(SOURCE.read_text(encoding="utf-8"))
    if args.check:
        actual = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if actual != expected:
            print(f"stale generated file: {TARGET}")
            return 1
        print("CUSTOM-INSTRUCTIONS.md is current")
        return 0
    TARGET.write_text(expected, encoding="utf-8")
    print(f"generated {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
