import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_readmes_cross_link_and_state_capability_boundary(self):
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("README.zh-CN.md", english)
        self.assertIn("README.md", chinese)
        self.assertIn("not a runtime LLM gateway or automatic model router", english)
        self.assertIn("does not control ChatGPT's model picker", english)
        self.assertIn("Unknown is advisory, not blocking", english)
        self.assertIn("不是运行时 LLM Gateway", chinese)
        self.assertIn("UNVERIFIED", chinese)

    def test_docs_do_not_claim_automatic_switching(self):
        for filename in ("README.md", "README.zh-CN.md", "CUSTOM-INSTRUCTIONS.md", "SKILL.md"):
            text = (ROOT / filename).read_text(encoding="utf-8").lower()
            self.assertNotIn("automatically switches chatgpt", text)
            self.assertNotIn("自动切换 chatgpt 模型", text)

    def test_readmes_present_core_before_runtime_adapter(self):
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        for text in (english, chinese):
            self.assertIn("CUSTOM-INSTRUCTIONS.md", text)
            self.assertIn("Runtime adapters", text)
            self.assertIn("Product lifecycle", text)
            self.assertIn("HandoffGuard-Installer-v0.1.0.exe", text)
        self.assertIn("It is more than a static prompt", english)
        self.assertIn("Custom Instructions are one lightweight runtime adapter", english)
        self.assertIn("它不只是一段静态提示词", chinese)
        self.assertIn("Custom Instructions 只是", chinese)

    def test_readmes_document_safe_installer_lifecycle(self):
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        for phrase in ("Install", "Update", "Uninstall", "Repair", "Backup", "Verification"):
            self.assertIn(phrase, english)
        for phrase in ("安装", "升级", "卸载", "修复", "备份", "验证"):
            self.assertIn(phrase, chinese)
        self.assertIn("does not read chat history", english)
        self.assertIn("不读取聊天记录", chinese)

    def test_emission_gate_is_present_in_both_skills_and_readmes(self):
        root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        canonical_skill = (ROOT / "skills" / "handoff-guard" / "SKILL.md").read_text(encoding="utf-8")
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        for text in (root_skill, canonical_skill, english):
            self.assertRegex(text.lower(), r"work.{0,80}implementation environment")
            self.assertRegex(text.lower(), r"explicit.{0,80}(request|user)")
        self.assertIn("Work / implementation 环境", chinese)
        self.assertIn("明确要求", chinese)
        self.assertIn("Do not append a new Work handoff", root_skill)
        self.assertIn("fail closed", root_skill)
        self.assertIn("递归生成", chinese)


if __name__ == "__main__":
    unittest.main()
