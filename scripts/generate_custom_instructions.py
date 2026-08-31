#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runtime" / "custom-instructions.txt"
ENGLISH_SOURCE = ROOT / "runtime" / "custom-instructions.en.txt"
TARGET = ROOT / "CUSTOM-INSTRUCTIONS.md"
ENGLISH_TARGET = ROOT / "CUSTOM-INSTRUCTIONS.en.md"


def render(payload: str, language: str) -> str:
    if language == "en":
        return f"""# Handoff Guard — Manual ChatGPT installation

This is a generated English manual-installation artifact for the ChatGPT runtime adapter. Handoff Guard Core—not this document—is the product's canonical behavior layer. This page is generated from `runtime/custom-instructions.en.txt`; the Windows Guided Install executable and the default manual-installation page use the Chinese runtime source, so there is no separate installer policy.

Paste only the following block into ChatGPT Settings → Personalization → Custom Instructions. Preserve any unrelated instructions already present.

```text
{payload.strip()}
```

The runtime adapter is advisory: it cannot switch models, inspect provider APIs, or execute repository scripts. Use the Windows Guided Install executable to generate and copy local managed-block text, then manually paste and save it in ChatGPT. The executable does not modify, verify, back up, repair, or uninstall ChatGPT account settings.
"""
    if language == "zh":
        return f"""# Handoff Guard — ChatGPT 中文手动安装

这是一份为 ChatGPT 运行适配层生成的中文手动安装文件。Handoff Guard Core（而不是本文件）才是产品的 canonical behavior layer。Windows Guided Install 可执行文件和本页面都读取 `runtime/custom-instructions.txt`，因此安装器不会维护另一套独立策略。

请只复制下面的区块到 ChatGPT 的 `Settings → Personalization → Custom Instructions`。请保留已有的其他指令，不要覆盖无关内容。

```text
{payload.strip()}
```

运行适配层只提供建议：它不能切换模型、检查提供方 API，也不能执行仓库脚本。请使用 Windows Guided Install 在本地生成并复制管理区块，再手动粘贴到 ChatGPT 并保存。可执行文件不会修改、验证、备份、修复或卸载 ChatGPT 账户设置。
"""
    raise ValueError(f"unsupported language: {language}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the manual ChatGPT installation document")
    parser.add_argument("--check", action="store_true", help="fail if the generated document is stale")
    args = parser.parse_args()
    artifacts = (
        (SOURCE, TARGET, "zh"),
        (ENGLISH_SOURCE, ENGLISH_TARGET, "en"),
    )
    if args.check:
        stale = []
        for source, target, language in artifacts:
            expected = render(source.read_text(encoding="utf-8"), language)
            actual = target.read_text(encoding="utf-8") if target.exists() else ""
            if actual != expected:
                stale.append(str(target))
        if stale:
            print("stale generated file(s): " + ", ".join(stale))
            return 1
        print("Generated Custom Instructions artifacts are current")
        return 0
    for source, target, language in artifacts:
        target.write_text(render(source.read_text(encoding="utf-8"), language), encoding="utf-8")
        print(f"generated {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
