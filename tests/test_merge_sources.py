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
    def make_scoped_verification_case(self, root: Path, entries: list[dict]) -> Path:
        case_dir = root / "case"
        case_dir.mkdir()
        (case_dir / "events.jsonl").write_text("", encoding="utf-8")
        for agent_id, citation in (
            ("legal-research-agent", "테스트법 A 제1조"),
            ("data-protection-agent", "테스트법 B 제2조"),
        ):
            (case_dir / f"{agent_id}-meta.json").write_text(
                json.dumps(
                    {
                        "summary": "s",
                        "key_findings": [],
                        "sources": [
                            {"id": "src_001", "title": f"{agent_id} source", "grade": "A", "citation": citation}
                        ],
                        "error": None,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        (case_dir / "review-meta.json").write_text(
            json.dumps(
                {
                    "approval": "approved",
                    "summary": "s",
                    "comments": [],
                    "citation_verification": entries,
                    "error": None,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return case_dir

    def merged_statuses(self, case_dir: Path) -> dict[str, str]:
        result = subprocess.run(
            [sys.executable, str(CLI), str(case_dir)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads((case_dir / "sources.json").read_text(encoding="utf-8"))
        return {
            agent["agent_id"]: agent["sources"][0]["verification_status"]
            for agent in payload["agents"]
        }

    def make_verification_case(self, root: Path, citation_verification: list) -> Path:
        case_dir = root / "case"
        case_dir.mkdir()
        (case_dir / "events.jsonl").write_text("", encoding="utf-8")
        (case_dir / "legal-research-agent-meta.json").write_text(
            json.dumps(
                {
                    "summary": "s",
                    "key_findings": [],
                    "sources": [
                        {"id": "src_001", "title": "테스트법", "grade": "A", "citation": "테스트법 제1조"}
                    ],
                    "error": None,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (case_dir / "review-meta.json").write_text(
            json.dumps(
                {
                    "approval": "approved",
                    "summary": "s",
                    "comments": [],
                    "citation_verification": citation_verification,
                    "error": None,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return case_dir

    def test_sources_json_carries_verification_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = self.make_verification_case(
                Path(directory),
                [{"source_id": "src_001", "citation": "테스트법 제1조", "status": "verified"}],
            )
            result = subprocess.run(
                [sys.executable, str(CLI), str(case_dir)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads((case_dir / "sources.json").read_text(encoding="utf-8"))

        agents = {agent["agent_id"]: agent for agent in payload["agents"]}
        source = agents["legal-research-agent"]["sources"][0]
        self.assertEqual(source["verification_status"], "verified")
        self.assertEqual(
            payload["verification_summary"],
            {"nonexistent": 0, "not_checked": 0, "unverified": 0, "verified": 1},
        )

    def test_unmatched_source_defaults_to_not_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = self.make_verification_case(Path(directory), [])
            result = subprocess.run(
                [sys.executable, str(CLI), str(case_dir)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads((case_dir / "sources.json").read_text(encoding="utf-8"))

        agents = {agent["agent_id"]: agent for agent in payload["agents"]}
        source = agents["legal-research-agent"]["sources"][0]
        self.assertEqual(source["verification_status"], "not_checked")
        self.assertEqual(payload["verification_summary"]["not_checked"], 1)

    def test_same_source_id_is_scoped_by_agent_and_order_independent(self) -> None:
        entries = [
            {
                "agent_id": "legal-research-agent",
                "source_id": "src_001",
                "citation": "테스트법 A 제1조",
                "status": "verified",
            },
            {
                "agent_id": "data-protection-agent",
                "source_id": "src_001",
                "citation": "테스트법 B 제2조",
                "status": "nonexistent",
            },
        ]
        for ordered in (entries, list(reversed(entries))):
            with self.subTest(order=[entry["agent_id"] for entry in ordered]):
                with tempfile.TemporaryDirectory() as directory:
                    case_dir = self.make_scoped_verification_case(Path(directory), ordered)
                    statuses = self.merged_statuses(case_dir)
                self.assertEqual(statuses["legal-research-agent"], "verified")
                self.assertEqual(statuses["data-protection-agent"], "nonexistent")

    def test_conflicting_scoped_statuses_choose_worst(self) -> None:
        entries = [
            {
                "agent_id": "legal-research-agent",
                "source_id": "src_001",
                "citation": "테스트법 A 제1조",
                "status": status,
            }
            for status in ("verified", "unverified", "nonexistent")
        ]
        with tempfile.TemporaryDirectory() as directory:
            case_dir = self.make_scoped_verification_case(Path(directory), entries)
            statuses = self.merged_statuses(case_dir)
        self.assertEqual(statuses["legal-research-agent"], "nonexistent")

    def test_legacy_entry_ignores_global_source_id_and_matches_citation_only(self) -> None:
        entries = [
            {
                "source_id": "src_001",
                "citation": "테스트법 B 제2조",
                "status": "unverified",
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            case_dir = self.make_scoped_verification_case(Path(directory), entries)
            statuses = self.merged_statuses(case_dir)
        self.assertEqual(statuses["legal-research-agent"], "not_checked")
        self.assertEqual(statuses["data-protection-agent"], "unverified")

    def test_agent_scoped_citation_matches_without_source_id(self) -> None:
        entries = [
            {
                "agent_id": "data-protection-agent",
                "citation": "테스트법 B 제2조",
                "status": "unverified",
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            case_dir = self.make_scoped_verification_case(Path(directory), entries)
            statuses = self.merged_statuses(case_dir)
        self.assertEqual(statuses["legal-research-agent"], "not_checked")
        self.assertEqual(statuses["data-protection-agent"], "unverified")

    def test_scoped_source_id_takes_precedence_over_mismatched_citation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            case_dir.mkdir()
            (case_dir / "events.jsonl").write_text("", encoding="utf-8")
            (case_dir / "legal-research-agent-meta.json").write_text(
                json.dumps(
                    {
                        "summary": "s",
                        "key_findings": [],
                        "sources": [
                            {"id": "src_001", "title": "A", "grade": "A", "citation": "Citation A"},
                            {"id": "src_002", "title": "B", "grade": "A", "citation": "Citation B"},
                        ],
                        "error": None,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (case_dir / "review-meta.json").write_text(
                json.dumps(
                    {
                        "approval": "approved",
                        "summary": "s",
                        "comments": [],
                        "citation_verification": [
                            {
                                "agent_id": "legal-research-agent",
                                "source_id": "src_001",
                                "citation": "Citation B",
                                "status": "unverified",
                            }
                        ],
                        "error": None,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(CLI), str(case_dir)],
                capture_output=True, text=True, check=False,
            )
            payload = json.loads((case_dir / "sources.json").read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        sources = {source["id"]: source for source in payload["agents"][0]["sources"]}
        self.assertEqual(sources["src_001"]["verification_status"], "unverified")
        self.assertEqual(sources["src_002"]["verification_status"], "not_checked")

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
