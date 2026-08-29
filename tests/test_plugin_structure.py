import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PluginStructureTests(unittest.TestCase):
    def test_manifest_and_canonical_skill_are_present(self):
        manifest_path = ROOT / ".codex-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "handoff-guard")
        self.assertEqual(manifest["version"], "0.1.0")
        self.assertEqual(manifest["skills"], "./skills/")
        expected = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for source, target in (
            ("references/handoff-spec.md", "../../references/handoff-spec.md"),
            ("assets/handoff-template.md", "../../assets/handoff-template.md"),
            ("scripts/select_model.py", "../../scripts/select_model.py"),
            ("references/routing-policy.md", "../../references/routing-policy.md"),
            ("references/provider-profiles.md", "../../references/provider-profiles.md"),
            ("references/provider-profiles.json", "../../references/provider-profiles.json"),
            ("scripts/validate_handoff.py", "../../scripts/validate_handoff.py"),
        ):
            expected = expected.replace(source, target)
        self.assertEqual(
            (ROOT / "skills" / "handoff-guard" / "SKILL.md").read_text(encoding="utf-8"),
            expected,
        )

    def test_plugin_is_skills_only(self):
        self.assertFalse((ROOT / ".mcp.json").exists())
        self.assertFalse((ROOT / ".app.json").exists())
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertNotIn("mcpServers", manifest)
        self.assertNotIn("apps", manifest)

    def test_installer_and_plugin_versions_match(self):
        from handoff_guard_installer.managed_block import MANAGED_VERSION

        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(MANAGED_VERSION, manifest["version"])
        self.assertIn(f"v{MANAGED_VERSION}", (ROOT / "scripts" / "build_installer.ps1").read_text())

    def test_reused_resources_resolve_from_canonical_skill(self):
        skill_root = ROOT / "skills" / "handoff-guard"
        for relative in (
            "../../references/handoff-spec.md",
            "../../references/routing-policy.md",
            "../../references/provider-profiles.json",
            "../../assets/handoff-template.md",
            "../../scripts/select_model.py",
            "../../scripts/validate_handoff.py",
        ):
            self.assertTrue((skill_root / relative).resolve().is_file(), relative)

    def test_submission_fixture_has_seven_positive_and_eight_negative_cases(self):
        fixture = json.loads(
            (ROOT / "evals" / "plugin-submission-tests.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(fixture["positive"]), 7)
        self.assertEqual(len(fixture["negative"]), 8)
        self.assertTrue(any("UNVERIFIED" in item["expected"] for item in fixture["positive"]))


if __name__ == "__main__":
    unittest.main()
