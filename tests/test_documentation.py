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
        self.assertIn("未验证", chinese)

    def test_docs_do_not_claim_automatic_switching(self):
        for filename in ("README.md", "README.zh-CN.md", "SKILL.md"):
            text = (ROOT / filename).read_text(encoding="utf-8").lower()
            self.assertNotIn("automatically switches chatgpt", text)
            self.assertNotIn("自动切换 chatgpt 模型", text)

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
        self.assertIn("不会递归生成", chinese)


if __name__ == "__main__":
    unittest.main()
