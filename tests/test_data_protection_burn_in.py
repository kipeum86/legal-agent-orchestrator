from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BURN_IN_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "routing" / "data-protection-burn-in.json"
ROUTING_SCHEMA = REPO_ROOT / "schemas" / "routing.schema.json"

import sys

sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.routing import select_route  # noqa: E402


class DataProtectionBurnInTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_profile = os.environ.pop("LEGAL_ORCHESTRATOR_AGENT_PROFILE", None)
        self.cases = json.loads(BURN_IN_FIXTURE.read_text(encoding="utf-8"))

    def tearDown(self) -> None:
        if self._old_profile is None:
            os.environ.pop("LEGAL_ORCHESTRATOR_AGENT_PROFILE", None)
        else:
            os.environ["LEGAL_ORCHESTRATOR_AGENT_PROFILE"] = self._old_profile

    def test_schema_accepts_us_ca_jurisdiction(self) -> None:
        schema = json.loads(ROUTING_SCHEMA.read_text(encoding="utf-8"))
        enum = schema["properties"]["jurisdictions"]["items"]["enum"]
        self.assertIn("US-CA", enum)
        self.assertIn("California", enum)

    def test_default_profile_keeps_legacy_privacy_routes(self) -> None:
        os.environ.pop("LEGAL_ORCHESTRATOR_AGENT_PROFILE", None)
        for case in self.cases:
            with self.subTest(case=case["id"]):
                route = select_route(case["classification"])
                self.assertEqual(route["pipeline"], case["legacy_pipeline"])
                self.assertNotIn("data-protection-agent", route["pipeline"])
                self.assertNotIn("_merged", route["route_mode"])

    def test_merged_profile_routes_burn_in_cases_to_data_protection_agent(self) -> None:
        os.environ["LEGAL_ORCHESTRATOR_AGENT_PROFILE"] = "merged"
        for case in self.cases:
            with self.subTest(case=case["id"]):
                route = select_route(case["classification"])
                self.assertEqual(route["pipeline"], case["merged_pipeline"])
                self.assertEqual(route["route_mode"], case["merged_route_mode"])
                self.assertIn("data-protection-agent", route["pipeline"])
                self.assertNotIn("PIPA-expert", route["pipeline"])
                self.assertNotIn("GDPR-expert", route["pipeline"])

    def test_invalid_profile_falls_back_to_legacy(self) -> None:
        os.environ["LEGAL_ORCHESTRATOR_AGENT_PROFILE"] = "MERGED_UNAPPROVED"
        case = next(item for item in self.cases if item["id"] == "kr-eu-overseas-transfer-comparison")
        route = select_route(case["classification"])
        self.assertEqual(route["pipeline"], case["legacy_pipeline"])
        self.assertEqual(route["route_mode"], "multi_jurisdiction_data")

    def test_debate_privacy_cases_keep_legacy_participants_during_burn_in(self) -> None:
        os.environ["LEGAL_ORCHESTRATOR_AGENT_PROFILE"] = "merged"
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
        self.assertEqual(route["debate_participants"], ["PIPA-expert", "GDPR-expert"])
        self.assertNotIn("data-protection-agent", route["debate_participants"])


if __name__ == "__main__":
    unittest.main()
