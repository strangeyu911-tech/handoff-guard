import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HandoffEmissionPolicyFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(
            (ROOT / "evals" / "plugin-submission-tests.json").read_text(encoding="utf-8")
        )
        cls.positive = {item["id"]: item for item in cls.fixture["positive"]}
        cls.negative = {item["id"]: item for item in cls.fixture["negative"]}

    def test_positive_emission_cases(self):
        self.assertIn("positive-chat-settled-decision", self.positive)
        self.assertIn("positive-explicit-handoff-request", self.positive)
        for case_id in ("positive-chat-settled-decision", "positive-explicit-handoff-request"):
            self.assertIn("can generate", self.positive[case_id]["expected"].lower())

    def test_work_and_uncertain_cases_are_no_recursion_cases(self):
        expected_ids = {
            "negative-work-file-edit-complete",
            "negative-work-tests-complete",
            "negative-work-commit-complete",
            "negative-uncertain-with-implementation-signals",
            "negative-work-next-stage-plan",
        }
        self.assertTrue(expected_ids.issubset(self.negative))
        for case_id in expected_ids:
            expected = self.negative[case_id]["expected"].lower()
            self.assertIn("do not", expected)
            self.assertIn("handoff", expected)

    def test_fixture_keeps_model_regressions(self):
        self.assertIn("positive-unknown-model-preflight", self.positive)
        self.assertIn("positive-material-mismatch", self.positive)
        self.assertIn("unverified", self.positive["positive-unknown-model-preflight"]["expected"].lower())
        self.assertIn("block", self.positive["positive-material-mismatch"]["expected"].lower())


if __name__ == "__main__":
    unittest.main()
