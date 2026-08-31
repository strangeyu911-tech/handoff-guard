import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CustomInstructionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "CUSTOM-INSTRUCTIONS.md").read_text(encoding="utf-8")
        cls.instructions = cls._extract_payload(cls.source, "CUSTOM-INSTRUCTIONS.md")
        cls.english_source = (ROOT / "CUSTOM-INSTRUCTIONS.en.md").read_text(encoding="utf-8")
        cls.english_instructions = cls._extract_payload(cls.english_source, "CUSTOM-INSTRUCTIONS.en.md")

    @staticmethod
    def _extract_payload(source, filename):
        match = re.search(r"```text\n(.*?)\n```", source, re.DOTALL)
        if not match:
            raise AssertionError(f"{filename} must contain one paste-ready text block")
        return match.group(1)

    def test_generated_manual_artifact_matches_canonical_runtime_template(self):
        canonical = (ROOT / "runtime" / "custom-instructions.txt").read_text(encoding="utf-8").strip()
        self.assertEqual(self.instructions, canonical)

    def test_generated_english_manual_artifact_matches_english_runtime_template(self):
        canonical = (ROOT / "runtime" / "custom-instructions.en.txt").read_text(encoding="utf-8").strip()
        self.assertEqual(self.english_instructions, canonical)

    def test_installer_loads_the_same_canonical_template(self):
        from handoff_guard_installer.managed_block import canonical_payload

        self.assertEqual(self.instructions, canonical_payload())

    def test_paste_ready_block_fits_plus_limit(self):
        self.assertLessEqual(len(self.instructions), 5000)
        self.assertLessEqual(len(self.english_instructions), 5000)

    def test_surface_gate_and_handoff_schema_are_present(self):
        required = (
            "普通 Chat / discussion",
            "Work / implementation 环境",
            "不要在这里追加新的 Work handoff",
            "用户明确要求生成 handoff 时，可以覆盖这一自动触发限制",
            "Recommended model",
            "Reasoning effort",
            "Preflight",
            "Current state",
            "Completed",
            "Checkpoint",
            "Next objective",
            "Locked decisions / boundaries",
            "Do-not / guardrails",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.instructions)

    def test_routing_dimensions_and_recent_regressions_are_present(self):
        required = (
            "operation_mode",
            "task_complexity",
            "decision_novelty",
            "ambiguity",
            "blast_radius",
            "irreversibility",
            "cross_system_contract",
            "data_integrity_risk",
            "destructive",
            "prior_failed_attempts",
            "复杂度本身不能把任务升级到 Sol tier",
            "已确定架构上的实施",
            "可逆迁移使用 Luna tier",
            "破坏性或高不可逆迁移使用 Sol tier",
            "Medium 与 High reasoning effort 的差异本身不能触发 BLOCK",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.instructions)

    def test_unknown_metadata_remains_advisory(self):
        self.assertIn("返回 UNVERIFIED", self.instructions)
        self.assertIn("允许继续执行", self.instructions)
        self.assertIn("才返回 BLOCK", self.instructions)

    def test_english_manual_artifact_preserves_protocol_and_routing_terms(self):
        required = (
            "ordinary Chat / discussion",
            "Work / implementation environment",
            "Do not append a new Work handoff",
            "An explicit request to generate a handoff overrides this gate",
            "Recommended model",
            "Reasoning effort",
            "Complexity alone never makes a task Sol-tier",
            "A reversible migration is Luna-tier",
            "A destructive or high-irreversibility migration is Sol-tier",
            "Medium versus High reasoning effort alone never blocks",
            "report UNVERIFIED",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.english_instructions)


if __name__ == "__main__":
    unittest.main()
