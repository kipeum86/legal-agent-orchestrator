from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "routing" / "classification-cases.json"
CLI = REPO_ROOT / "scripts" / "select-route.py"
sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.routing import normalize_classification, select_route  # noqa: E402


class RoutingTests(unittest.TestCase):
    def test_fixture_routes_match_expected_pipeline(self) -> None:
        cases = json.loads(FIXTURE.read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["name"]):
                route = select_route(case["classification"])
                self.assertEqual(route["pattern"], case["expected_pattern"])
                self.assertEqual(route["pipeline"], case["expected_pipeline"])
                if "expected_route_mode" in case:
                    self.assertEqual(route["route_mode"], case["expected_route_mode"])
                if "expected_parallel_agents" in case:
                    self.assertEqual(route["parallel_agents"], case["expected_parallel_agents"])

    def test_legacy_plus_delimited_values_normalize_to_arrays(self) -> None:
        normalized = normalize_classification(
            {
                "jurisdiction": ["KR", "EU"],
                "domain": "contract+translation",
                "task": "contract_review+translation",
                "complexity": "compound",
            }
        )
        self.assertEqual(normalized["domains"], ["contract", "translation"])
        self.assertEqual(normalized["tasks"], ["contract_review", "translation"])

    def test_contract_drafting_takes_precedence_over_contract_review(self) -> None:
        route = select_route(
            {
                "jurisdictions": [],
                "domains": ["contract"],
                "tasks": ["drafting"],
                "complexity": "compound",
                "confidence": 1.0,
            }
        )
        self.assertEqual(route["route_mode"], "contract_drafting_wf5")
        self.assertNotEqual(route["route_mode"], "contract_review")

    def test_kr_eu_privacy_routes_to_data_protection_agent(self) -> None:
        route = select_route(
            {
                "jurisdictions": ["KR", "EU"],
                "domains": ["data_protection"],
                "tasks": ["research"],
                "complexity": "multi_domain",
                "confidence": 1.0,
            }
        )
        self.assertEqual(route["route_mode"], "multi_jurisdiction_data")
        self.assertEqual(
            route["pipeline"],
            ["data-protection-agent", "legal-writing-agent", "second-review-agent"],
        )
        self.assertNotIn("PIPA-expert", route["pipeline"])
        self.assertNotIn("GDPR-expert", route["pipeline"])

    def test_california_privacy_routes_to_data_protection_agent(self) -> None:
        route = select_route(
            {
                "jurisdictions": ["US-CA"],
                "domains": ["data_protection"],
                "tasks": ["research"],
                "complexity": "simple",
                "confidence": 1.0,
            }
        )
        self.assertEqual(route["route_mode"], "single_jurisdiction_data")
        self.assertEqual(
            route["pipeline"],
            ["data-protection-agent", "legal-writing-agent", "second-review-agent"],
        )

    def test_cli_reads_classification_file(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CLI), str(FIXTURE)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)

        first_case = json.loads(FIXTURE.read_text(encoding="utf-8"))[0]["classification"]
        temp = REPO_ROOT / "tests" / "fixtures" / "routing" / ".tmp-single-classification.json"
        try:
            temp.write_text(json.dumps(first_case), encoding="utf-8")
            ok = subprocess.run(
                [sys.executable, str(CLI), str(temp)],
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            temp.unlink(missing_ok=True)
        self.assertEqual(ok.returncode, 0, msg=ok.stderr)
        self.assertEqual(json.loads(ok.stdout)["route_mode"], "game_regulation")


if __name__ == "__main__":
    unittest.main()
