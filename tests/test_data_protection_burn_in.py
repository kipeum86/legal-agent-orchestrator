from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BURN_IN_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "routing" / "data-protection-burn-in.json"
ROUTING_SCHEMA = REPO_ROOT / "schemas" / "routing.schema.json"

sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.routing import select_route  # noqa: E402


class DataProtectionBurnInTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = json.loads(BURN_IN_FIXTURE.read_text(encoding="utf-8"))

    def test_schema_accepts_us_ca_jurisdiction(self) -> None:
        schema = json.loads(ROUTING_SCHEMA.read_text(encoding="utf-8"))
        enum = schema["properties"]["jurisdictions"]["items"]["enum"]
        self.assertIn("US-CA", enum)
        self.assertIn("California", enum)

    def test_burn_in_cases_route_to_data_protection_agent(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["id"]):
                route = select_route(case["classification"])
                self.assertEqual(route["pipeline"], case["expected_pipeline"])
                self.assertEqual(route["route_mode"], case["expected_route_mode"])
                self.assertIn("data-protection-agent", route["pipeline"])
                self.assertNotIn("PIPA-expert", route["pipeline"])
                self.assertNotIn("GDPR-expert", route["pipeline"])
                if "expected_agent_research_mode" in case:
                    self.assertEqual(
                        route.get("agent_research_mode"),
                        case["expected_agent_research_mode"],
                    )

    def test_debate_privacy_pairs_data_protection_with_general_research(self) -> None:
        route = select_route(
            {
                "jurisdictions": ["KR", "EU"],
                "domains": ["data_protection"],
                "tasks": ["debate"],
                "complexity": "adversarial",
                "confidence": 0.95,
                "ambiguity": [],
            }
        )
        self.assertEqual(route["route_mode"], "adversarial_debate")
        self.assertEqual(
            route["debate_participants"],
            ["data-protection-agent", "legal-research-agent"],
        )
        self.assertNotIn("PIPA-expert", route["debate_participants"])
        self.assertNotIn("GDPR-expert", route["debate_participants"])


if __name__ == "__main__":
    unittest.main()
