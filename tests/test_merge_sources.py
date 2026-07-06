from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI = REPO_ROOT / "scripts" / "merge-sources.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "cases" / "pattern1-multi-agent"


class MergeSourcesTests(unittest.TestCase):
    def test_merges_multi_agent_meta_and_events_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            shutil.copytree(FIXTURE, case_dir)
            result = subprocess.run(
                [sys.executable, str(CLI), str(case_dir)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads((case_dir / "sources.json").read_text(encoding="utf-8"))

        self.assertEqual(payload["total_sources"], 3)
        self.assertEqual(payload["grade_distribution"], {"A": 3, "B": 0, "C": 0, "D": 0})
        agents = {agent["agent_id"]: agent for agent in payload["agents"]}
        self.assertEqual(set(agents), {"data-protection-agent", "legal-research-agent"})
        dp_citations = [s["citation"] for s in agents["data-protection-agent"]["sources"]]
        self.assertIn("제28조의8", dp_citations)
        self.assertIn("Article 28", dp_citations)
        self.assertEqual(
            agents["legal-research-agent"]["sources"][0]["citation"], "Article 25"
        )

    def test_debate_round_meta_uses_real_agent_id_for_deduplication(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            case_dir.mkdir()
            source = {
                "title": "Personal Information Protection Act",
                "grade": "A",
                "citation": "Article 28-8",
            }
            (case_dir / "debate-round-1-data-protection-agent-meta.json").write_text(
                json.dumps(
                    {
                        "round": 1,
                        "summary": "opening",
                        "key_findings": ["finding"],
                        "sources": [source],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            event = {
                "id": "evt_001",
                "agent": "data-protection-agent",
                "type": "source_graded",
                "data": {
                    "agent_id": "data-protection-agent",
                    "source": source["title"],
                    "grade": source["grade"],
                    "citation": source["citation"],
                },
            }
            (case_dir / "events.jsonl").write_text(
                json.dumps(event, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(CLI), str(case_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads((case_dir / "sources.json").read_text(encoding="utf-8"))

        self.assertEqual(payload["total_sources"], 1)
        self.assertEqual(payload["grade_distribution"], {"A": 1, "B": 0, "C": 0, "D": 0})
        self.assertEqual(len(payload["agents"]), 1)
        self.assertEqual(payload["agents"][0]["agent_id"], "data-protection-agent")

    def test_corrupt_existing_meta_file_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            case_dir.mkdir()
            (case_dir / "legal-research-agent-meta.json").write_text("{bad-json", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(CLI), str(case_dir)],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("skipped meta files", result.stderr)
        self.assertIn("legal-research-agent-meta.json", result.stderr)


if __name__ == "__main__":
    unittest.main()
