import copy
import json
import unittest
from pathlib import Path

from handoff_guard_core import (
    ExecutionContract,
    export_markdown,
    import_markdown,
    migrate_contract,
    validate_contract,
    validate_mutation,
)


ROOT = Path(__file__).resolve().parents[1]


def valid_payload():
    return {
        "contract_version": "1.0",
        "handoff_id": "hg-test-001",
        "source_context": {"status": "known", "surface": "chat", "summary": "Settled implementation request.", "provenance": "test-fixture"},
        "objective": {"statement": "Implement the contract foundation.", "requires": ["contract"]},
        "current_state": {"status": "known", "summary": "Phase 0 is complete.", "completed": ["Evidence baseline repaired."]},
        "checkpoint": {"status": "present", "reference": "afe3d99"},
        "locked_decisions": [{"id": "core-boundary", "decision": "Core owns contract semantics.", "subject": "contract", "effect": "allow"}],
        "mutable_implementation_choices": [{"id": "representation", "choice": "Use standard-library dataclasses."}],
        "constraints": [{"id": "no-executor", "type": "must_not", "subject": "executor"}],
        "do_not": [{"id": "no-transport", "rule": "Do not start transport.", "subject": "transport", "action": "prohibit"}],
        "context_manifest": {"items": [{"path": "docs/roadmap.md", "provenance": "repository"}], "omissions": [], "budget": {"status": "known", "unit": "tokens", "limit": 8000}},
        "execution_surface": "codex",
        "model": {"status": "known", "name": "Luna", "tier": "general"},
        "reasoning_effort": "medium",
        "sandbox": {"status": "known", "mode": "workspace-write", "network": "blocked"},
        "approval_requirements": {"status": "known", "mode": "explicit", "required": True, "reasons": ["External side effects require review."]},
        "preflight": {"status": "PASS", "evidence": ["Current model is suitable."]},
        "acceptance_criteria": [{"id": "tests", "description": "The bundled contract tests pass.", "required": True, "evidence": [{"type": "test", "status": "known", "observable": "unittest reports zero failures.", "value": "0 failures"}]}],
        "result_schema": {"version": "1.0", "states": ["complete", "partial", "blocked", "unknown"], "evidence_fields": ["observable", "unknowns"]},
        "retry_policy": None,
    }


class ContractTests(unittest.TestCase):
    def test_minimal_valid_contract(self):
        payload = valid_payload()
        payload["locked_decisions"] = []
        payload["mutable_implementation_choices"] = []
        payload["constraints"] = []
        payload["do_not"] = []
        payload["context_manifest"] = {"items": [], "omissions": [{"status": "unknown", "reason": "No context was supplied."}], "budget": {"status": "unknown"}}
        self.assertTrue(validate_contract(payload).valid)

    def test_fully_populated_contract_creates_typed_wrapper(self):
        contract = ExecutionContract.from_dict(valid_payload())
        self.assertEqual(contract.to_dict(), valid_payload())

    def test_missing_required_field_is_actionable(self):
        payload = valid_payload()
        del payload["result_schema"]
        result = validate_contract(payload)
        self.assertFalse(result.valid)
        self.assertTrue(any(error["code"] == "missing_required_field" and error["path"] == "result_schema" for error in result.errors))

    def test_explicit_unknown_state_is_valid(self):
        payload = valid_payload()
        payload["source_context"] = {"status": "unknown", "surface": "unknown", "summary": "Surface metadata unavailable.", "provenance": "test-fixture"}
        payload["sandbox"] = {"status": "UNVERIFIED", "mode": "unknown", "network": "unknown"}
        self.assertTrue(validate_contract(payload).valid)

    def test_implicit_unknown_state_is_rejected(self):
        payload = valid_payload()
        del payload["current_state"]["status"]
        result = validate_contract(payload)
        self.assertFalse(result.valid)
        self.assertTrue(any(error["code"] == "implicit_unknown" for error in result.errors))

    def test_locked_decision_and_objective_contradiction(self):
        payload = valid_payload()
        payload["locked_decisions"] = [{"id": "no-executor", "decision": "Executor must not start.", "subject": "executor", "effect": "prohibit"}]
        payload["objective"]["requires"] = ["executor"]
        result = validate_contract(payload)
        self.assertTrue(any(error["code"] == "contradiction" for error in result.errors))

    def test_do_not_conflict_is_rejected(self):
        payload = valid_payload()
        payload["objective"]["requires"] = ["browser"]
        payload["do_not"].append({"id": "no-browser", "rule": "Do not control a browser.", "subject": "browser", "action": "prohibit"})
        result = validate_contract(payload)
        self.assertTrue(any(error["code"] == "contradiction" for error in result.errors))

    def test_constraint_contradiction_is_rejected(self):
        payload = valid_payload()
        payload["constraints"] = [
            {"id": "must-a", "type": "must", "subject": "artifact"},
            {"id": "must-not-a", "type": "must_not", "subject": "artifact"},
        ]
        result = validate_contract(payload)
        self.assertTrue(any(error["code"] == "constraint_contradiction" for error in result.errors))

    def test_locked_decision_mutation_is_rejected(self):
        original = valid_payload()
        candidate = copy.deepcopy(original)
        candidate["locked_decisions"][0]["decision"] = "Core does not own contract semantics."
        result = validate_mutation(original, candidate)
        self.assertTrue(any(error["code"] == "locked_decision_mutation" for error in result.errors))

    def test_mutable_implementation_change_is_allowed(self):
        original = valid_payload()
        candidate = copy.deepcopy(original)
        candidate["mutable_implementation_choices"][0]["choice"] = "Use a typed mapping wrapper."
        self.assertTrue(validate_mutation(original, candidate).valid)

    def test_non_observable_acceptance_is_rejected(self):
        payload = valid_payload()
        payload["acceptance_criteria"] = [{"id": "weak", "description": "works", "required": True, "evidence": []}]
        result = validate_contract(payload)
        self.assertTrue(any(error["code"] == "non_observable_acceptance" for error in result.errors))

    def test_observable_acceptance_is_valid(self):
        self.assertTrue(validate_contract(valid_payload()).valid)

    def test_unsupported_contract_version_is_actionable(self):
        payload = valid_payload()
        payload["contract_version"] = "9.0"
        result = validate_contract(payload)
        self.assertTrue(any(error["code"] == "unsupported_contract_version" for error in result.errors))

    def test_migration_success_is_explicit(self):
        fixture = json.loads((ROOT / "evals" / "contract-migration-fixtures.json").read_text(encoding="utf-8"))["success"][0]
        migrated = migrate_contract(fixture["input"])
        self.assertEqual(migrated["contract_version"], "1.0")
        self.assertTrue(validate_contract(migrated).valid)
        self.assertEqual(migrated["source_context"]["status"], "unknown")
        self.assertEqual(migrated["handoff_id"], fixture["input"]["handoff_id"])

    def test_migration_failure_is_explicit(self):
        fixture = json.loads((ROOT / "evals" / "contract-migration-fixtures.json").read_text(encoding="utf-8"))["failure"][0]
        with self.assertRaisesRegex(ValueError, fixture["expected_error"]):
            migrate_contract(fixture["input"])

    def test_serialization_round_trip(self):
        payload = valid_payload()
        restored = json.loads(json.dumps(payload, ensure_ascii=False))
        self.assertEqual(ExecutionContract.from_dict(restored).to_dict(), payload)

    def test_markdown_import_supports_legacy_handoff(self):
        markdown = """# Handoff
## Recommended model
Luna
## Reasoning effort
medium
## Preflight
UNVERIFIED
## Current state
Phase 0 complete.
## Completed
- Repaired the baseline.
## Checkpoint
none
## Next objective
Implement Phase 1.
## Locked decisions / boundaries
- Core owns contract semantics.
## Do-not / guardrails
- Do not start an executor.
"""
        contract = import_markdown(markdown)
        self.assertEqual(contract.to_dict()["contract_version"], "1.0")
        self.assertEqual(contract.to_dict()["checkpoint"]["status"], "none")
        self.assertEqual(contract.to_dict()["source_context"]["status"], "unknown")

    def test_markdown_export_round_trip_uses_canonical_json(self):
        contract = ExecutionContract.from_dict(valid_payload())
        exported = export_markdown(contract)
        self.assertIn("## Canonical execution contract (JSON)", exported)
        self.assertEqual(import_markdown(exported).to_dict(), contract.to_dict())

    def test_malformed_source_context_is_rejected(self):
        payload = valid_payload()
        payload["source_context"] = {"surface": "chat", "summary": "Missing status."}
        result = validate_contract(payload)
        self.assertTrue(any(error["code"] == "implicit_unknown" and error["path"] == "source_context.status" for error in result.errors))

    def test_approval_semantics_are_validated(self):
        payload = valid_payload()
        payload["approval_requirements"] = {"status": "known", "mode": "none", "required": True}
        result = validate_contract(payload)
        self.assertTrue(any(error["code"] == "incompatible_fields" for error in result.errors))

    def test_sandbox_and_execution_surface_are_validated(self):
        payload = valid_payload()
        payload["execution_surface"] = "desktop"
        payload["sandbox"]["mode"] = "full-access"
        result = validate_contract(payload)
        self.assertGreaterEqual(sum(error["code"] == "invalid_value" for error in result.errors), 2)

    def test_schema_declares_phase_one_required_fields(self):
        schema = json.loads((ROOT / "schemas" / "execution-contract.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["contract_version"]["const"], "1.0")
        self.assertIn("acceptance_criteria", schema["required"])


if __name__ == "__main__":
    unittest.main()
