from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI = REPO_ROOT / "scripts" / "resolve-sync-targets.py"
sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.routing import select_route  # noqa: E402
from scripts.lib.sync_targets import resolve_sync_targets  # noqa: E402


class ResolveSyncTargetsTests(unittest.TestCase):
    def test_sequential_route_syncs_pipeline_agents(self) -> None:
        route = select_route(
            {
                "jurisdictions": ["KR"],
                "domains": ["game_regulation"],
                "tasks": ["research"],
                "complexity": "simple",
                "confidence": 1.0,
            }
        )

        self.assertEqual(
            resolve_sync_targets(route),
            ["legal-research-agent", "legal-writing-agent", "second-review-agent"],
        )

    def test_parallel_route_syncs_parallel_and_downstream_agents(self) -> None:
        route = select_route(
            {
                "jurisdictions": ["KR", "EU"],
                "domains": ["game_regulation", "data_protection"],
                "tasks": ["research"],
                "complexity": "multi_domain",
                "confidence": 1.0,
            }
        )

        self.assertEqual(
            resolve_sync_targets(route),
            [
                "legal-research-agent",
                "data-protection-agent",
                "legal-writing-agent",
                "second-review-agent",
            ],
        )

    def test_debate_route_syncs_participants_plus_writing_and_review(self) -> None:
        route = select_route(
            {
                "jurisdictions": ["KR", "EU"],
                "domains": ["data_protection"],
                "tasks": ["debate"],
                "complexity": "adversarial",
                "confidence": 1.0,
            }
        )

        self.assertEqual(
            resolve_sync_targets(route),
            [
                "data-protection-agent",
                "legal-research-agent",
                "legal-writing-agent",
                "second-review-agent",
            ],
        )

    def test_out_of_scope_route_has_no_sync_targets(self) -> None:
        route = select_route(
            {
                "jurisdictions": [],
                "domains": ["contract"],
                "tasks": ["contract_review"],
                "complexity": "compound",
                "confidence": 1.0,
            }
        )

        self.assertEqual(resolve_sync_targets(route), [])

    def test_needs_scope_route_has_no_sync_targets(self) -> None:
        route = select_route(
            {
                "jurisdictions": ["KR", "EU", "US-CA", "JP"],
                "domains": ["data_protection"],
                "tasks": ["research"],
                "complexity": "multi_domain",
                "confidence": 1.0,
            }
        )

        self.assertEqual(resolve_sync_targets(route), [])

    def test_control_plane_entries_are_dropped(self) -> None:
        route = {
            "pattern": "pattern_3",
            "execution": "debate",
            "pipeline": ["manage-debate"],
            "debate_participants": ["legal-research-agent", "data-protection-agent"],
        }

        self.assertEqual(
            resolve_sync_targets(route),
            [
                "legal-research-agent",
                "data-protection-agent",
                "legal-writing-agent",
                "second-review-agent",
            ],
        )

    def test_retired_agent_ids_are_rejected(self) -> None:
        route = {
            "pattern": "pattern_2",
            "execution": "sequential",
            "pipeline": ["general-legal-research"],
        }

        with self.assertRaisesRegex(ValueError, "retired agent/repo IDs"):
            resolve_sync_targets(route)

    def test_unknown_agent_ids_are_rejected(self) -> None:
        route = {
            "pattern": "pattern_2",
            "execution": "sequential",
            "pipeline": ["unknown-agent"],
        }

        with self.assertRaisesRegex(ValueError, "unknown sync target"):
            resolve_sync_targets(route)

    def test_cli_reads_route_file(self) -> None:
        route = select_route(
            {
                "jurisdictions": ["US-CA"],
                "domains": ["data_protection"],
                "tasks": ["research"],
                "complexity": "simple",
                "confidence": 1.0,
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "route.json"
            path.write_text(json.dumps(route), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(CLI), str(path)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            ["data-protection-agent", "legal-writing-agent", "second-review-agent"],
        )

    def test_cli_rejects_bad_shape(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CLI)],
            cwd=REPO_ROOT,
            input=json.dumps({"pipeline": "legal-research-agent"}),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("pipeline must be a JSON array", result.stderr)


if __name__ == "__main__":
    unittest.main()
