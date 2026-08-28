import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("select_model", ROOT / "scripts" / "select_model.py")
select_model = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(select_model)


class SelectModelTests(unittest.TestCase):
    def test_simple_docs_uses_budget(self):
        result = select_model.select({"task_complexity": "simple", "task_type": "docs", "provider_availability": ["codex"]})
        self.assertEqual(result["recommended_model_tier"], "budget")
        self.assertEqual(result["recommended_reasoning_effort"], "low")

    def test_settled_implementation_uses_general(self):
        result = select_model.select({"task_complexity": "moderate", "task_type": "implementation", "architecture_settled": True, "provider_availability": ["codex"]})
        self.assertEqual(result["recommended_model_tier"], "general")

    def test_known_suitable_model_passes(self):
        result = select_model.select({"task_complexity": "moderate", "task_type": "implementation", "current_model": {"provider": "codex", "tier": "general"}, "current_reasoning_effort": "medium", "provider_availability": ["codex"]})
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["preflight"]["status"], "PASS")
        self.assertTrue(result["execution_allowed"])

    def test_architecture_and_bugfix_use_strong(self):
        for task_type in ("architecture", "bugfix"):
            result = select_model.select({"task_complexity": "moderate", "task_type": task_type, "provider_availability": ["codex"]})
            self.assertEqual(result["recommended_model_tier"], "strong")

    def test_unsettled_architecture_uses_strong(self):
        result = select_model.select({"task_complexity": "moderate", "task_type": "implementation", "architecture_settled": False, "provider_availability": ["codex"]})
        self.assertEqual(result["recommended_model_tier"], "strong")

    def test_overpowered_current_model_blocks(self):
        result = select_model.select({"task_complexity": "simple", "task_type": "docs", "current_model": {"provider": "codex", "tier": "strong"}, "provider_availability": ["codex"]})
        self.assertTrue(result["block_current_execution"])
        self.assertIn("stronger", result["preflight"]["reason"])

    def test_underpowered_current_model_blocks(self):
        result = select_model.select({"task_complexity": "complex", "task_type": "bugfix", "current_model": {"provider": "codex", "tier": "budget"}, "provider_availability": ["codex"]})
        self.assertTrue(result["block_current_execution"])
        self.assertIn("weaker", result["preflight"]["reason"])

    def test_one_tier_reasoning_difference_does_not_block(self):
        result = select_model.select({"task_complexity": "moderate", "task_type": "implementation", "current_model": {"provider": "codex", "tier": "strong"}, "current_reasoning_effort": "high", "provider_availability": ["codex"]})
        self.assertFalse(result["block_current_execution"])
        self.assertEqual(result["status"], "PASS")

    def test_unknown_model_does_not_block_execution(self):
        result = select_model.select({"task_complexity": "moderate", "task_type": "implementation", "current_model": {"provider": "codex", "model": "unknown"}, "provider_availability": ["codex"]})
        self.assertFalse(result["block_current_execution"])
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertTrue(result["execution_allowed"])
        self.assertIn("does not expose", result["preflight"]["reason"])

    def test_missing_model_metadata_does_not_block_execution(self):
        result = select_model.select({"task_complexity": "moderate", "task_type": "implementation", "provider_availability": ["codex"]})
        self.assertFalse(result["block_current_execution"])
        self.assertEqual(result["preflight"]["status"], "UNVERIFIED")
        self.assertTrue(result["preflight"]["execution_allowed"])

    def test_unknown_reasoning_does_not_block(self):
        result = select_model.select({"task_complexity": "moderate", "task_type": "implementation", "current_model": {"provider": "codex", "tier": "general"}, "provider_availability": ["codex"]})
        self.assertFalse(result["block_current_execution"])
        self.assertEqual(result["status"], "UNVERIFIED")

    def test_quota_falls_back_to_workbuddy(self):
        result = select_model.select({"task_complexity": "moderate", "task_type": "implementation", "preferred_provider": "codex", "quota_unavailable": True, "quota_provider": "codex", "provider_availability": ["codex", "workbuddy"]})
        self.assertEqual(result["recommended_provider"], "workbuddy")

    def test_quota_fallback_with_unknown_model_does_not_block(self):
        result = select_model.select({"task_complexity": "moderate", "task_type": "implementation", "preferred_provider": "codex", "quota_unavailable": True, "quota_provider": "codex", "provider_availability": ["codex", "workbuddy"]})
        self.assertEqual(result["recommended_provider"], "workbuddy")
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertFalse(result["block_current_execution"])

    def test_preferred_workbuddy_wins(self):
        result = select_model.select({"task_complexity": "simple", "preferred_provider": "workbuddy", "provider_availability": ["codex", "workbuddy"]})
        self.assertEqual(result["recommended_provider"], "workbuddy")

    def test_preferred_workbuddy_still_wins_when_codex_quota_is_unavailable(self):
        result = select_model.select({"task_complexity": "simple", "preferred_provider": "workbuddy", "quota_unavailable": True, "provider_availability": ["codex", "workbuddy"]})
        self.assertEqual(result["recommended_provider"], "workbuddy")

    def test_model_catalog_can_change_without_selector_change(self):
        profiles = select_model.load_profiles()
        profiles["providers"]["workbuddy"]["models"] = [{"name": "NewBudget", "tier": "budget", "cost_class": "low", "capabilities": ["docs"]}]
        result = select_model.select({"task_complexity": "simple", "provider_availability": ["workbuddy"]}, profiles)
        self.assertEqual(result["recommended_model"], "NewBudget")

    def test_case_a_first_core_model_uses_sol_medium(self):
        result = select_model.select({
            "task_complexity": "complex",
            "task_type": "architecture",
            "operation_mode": "architecture",
            "decision_novelty": "high",
            "ambiguity": "high",
            "blast_radius": "high",
            "cross_system_contract": True,
            "provider_availability": ["codex"],
        })
        self.assertEqual(result["recommended_model"], "Sol")
        self.assertEqual(result["recommended_reasoning_effort"], "medium")

    def test_case_b_large_read_only_audit_uses_luna_medium(self):
        result = select_model.select({
            "task_complexity": "complex",
            "task_type": "research",
            "operation_mode": "read_only_audit",
            "provider_availability": ["codex"],
        })
        self.assertEqual(result["recommended_model"], "Luna")
        self.assertEqual(result["recommended_model_tier"], "general")
        self.assertEqual(result["recommended_reasoning_effort"], "medium")

    def test_complexity_alone_does_not_escalate(self):
        result = select_model.select({"task_complexity": "complex", "task_type": "other", "provider_availability": ["codex"]})
        self.assertEqual(result["recommended_model"], "Luna")
        self.assertEqual(result["recommended_model_tier"], "general")

    def test_low_risk_small_bug_uses_luna(self):
        result = select_model.select({
            "task_complexity": "moderate",
            "task_type": "bugfix",
            "operation_mode": "bugfix",
            "ambiguity": "low",
            "blast_radius": "low",
            "irreversibility": "low",
            "provider_availability": ["codex"],
        })
        self.assertEqual(result["recommended_model"], "Luna")

    def test_destructive_migration_uses_sol(self):
        result = select_model.select({
            "task_complexity": "moderate",
            "operation_mode": "migration",
            "irreversibility": "high",
            "data_integrity_risk": True,
            "destructive": True,
            "provider_availability": ["codex"],
        })
        self.assertEqual(result["recommended_model"], "Sol")

    def test_two_prior_failures_escalate_bugfix(self):
        result = select_model.select({
            "task_complexity": "complex",
            "operation_mode": "bugfix",
            "prior_failed_attempts": 2,
            "provider_availability": ["codex"],
        })
        self.assertEqual(result["recommended_model"], "Sol")

    def test_legacy_codex_model_name_remains_recognized(self):
        result = select_model.select({
            "task_complexity": "moderate",
            "current_model": {"provider": "codex", "model": "codex-general"},
            "current_reasoning_effort": "medium",
            "provider_availability": ["codex"],
        })
        self.assertEqual(result["status"], "PASS")

    def test_invalid_routing_dimension_fails_explicitly(self):
        with self.assertRaises(ValueError):
            select_model.select({"task_complexity": "moderate", "operation_mode": "unknown", "provider_availability": ["codex"]})


if __name__ == "__main__":
    unittest.main()
