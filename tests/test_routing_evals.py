import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("select_model", ROOT / "scripts" / "select_model.py")
select_model = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(select_model)


class RoutingEvalFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))

    def test_all_selector_fixtures_match_declared_expectations(self):
        for fixture in self.fixtures:
            if "input" not in fixture or "expect" not in fixture:
                continue
            with self.subTest(fixture=fixture["name"]):
                result = select_model.select(fixture["input"])
                for field, expected in fixture["expect"].items():
                    self.assertEqual(result.get(field), expected, field)


if __name__ == "__main__":
    unittest.main()
