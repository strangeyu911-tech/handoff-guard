import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CustomInstructionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "CUSTOM-INSTRUCTIONS.md").read_text(encoding="utf-8")
        match = re.search(r"```text\n(.*?)\n```", cls.source, re.DOTALL)
        if not match:
            raise AssertionError("CUSTOM-INSTRUCTIONS.md must contain one paste-ready text block")
        cls.instructions = match.group(1)

    def test_generated_manual_artifact_matches_canonical_runtime_template(self):
        canonical = (ROOT / "runtime" / "custom-instructions.txt").read_text(encoding="utf-8").strip()
        self.assertEqual(self.instructions, canonical)

    def test_installer_loads_the_same_canonical_template(self):
        from handoff_guard_installer.managed_block import canonical_payload

        self.assertEqual(self.instructions, canonical_payload())

    def test_paste_ready_block_fits_plus_limit(self):
        self.assertLessEqual(len(self.instructions), 5000)

    def test_surface_gate_and_handoff_schema_are_present(self):
        required = (
            "ordinary Chat / discussion",
            "Work / implementation environment",
            "Do not append a new Work handoff",
            "An explicit request to generate a handoff overrides this gate",
            "Recommended model",
            "Reasoning effort",
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
            "Complexity alone never makes a task Sol-tier",
            "implementation against a settled architecture",
            "A reversible migration is Luna-tier",
            "A destructive or high-irreversibility migration is Sol-tier",
            "Medium versus High reasoning effort alone never blocks",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.instructions)

    def test_unknown_metadata_remains_advisory(self):
        self.assertIn("report UNVERIFIED", self.instructions)
        self.assertIn("execution to continue", self.instructions)
        self.assertIn("BLOCK only", self.instructions)


if __name__ == "__main__":
    unittest.main()
