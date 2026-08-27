import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_handoff", ROOT / "scripts" / "validate_handoff.py")
validate_handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_handoff)


COMPLETE = """# Handoff
## Recommended model
Codex general
## Reasoning effort
medium
## Preflight
PASS
## Current state
Implementation is ready.
## Completed
- Added routing
## Checkpoint
abc123
## Next objective
Run tests.
## Locked decisions / boundaries
- Keep provider data configurable.
## Do-not / guardrails
- Do not re-plan architecture.
"""


class ValidateHandoffTests(unittest.TestCase):
    def test_complete_handoff_passes(self):
        result = validate_handoff.validate(COMPLETE)
        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])

    def test_missing_checkpoint_fails(self):
        result = validate_handoff.validate(COMPLETE.replace("## Checkpoint\nabc123", ""))
        self.assertFalse(result["valid"])
        self.assertIn("Missing required field: checkpoint", result["errors"])

    def test_empty_checkpoint_fails(self):
        result = validate_handoff.validate(COMPLETE.replace("abc123", ""))
        self.assertFalse(result["valid"])
        self.assertIn("Missing required field: checkpoint", result["errors"])

    def test_json_handoff_is_supported(self):
        payload = {"recommended_model": "codex-general", "reasoning_effort": "medium", "preflight": "PASS", "current_state": "ready", "completed": ["x"], "checkpoint": "none", "next_objective": "y", "locked_decisions": ["z"], "guardrails": ["do not expand"]}
        self.assertTrue(validate_handoff.validate(json.dumps(payload))["valid"])

    def test_json_empty_checkpoint_fails(self):
        payload = {"recommended_model": "codex-general", "reasoning_effort": "medium", "preflight": "PASS", "current_state": "ready", "completed": ["x"], "checkpoint": "", "next_objective": "y", "locked_decisions": ["z"], "guardrails": ["do not expand"]}
        result = validate_handoff.validate(json.dumps(payload))
        self.assertFalse(result["valid"])
        self.assertIn("Missing required field: checkpoint", result["errors"])


if __name__ == "__main__":
    unittest.main()
