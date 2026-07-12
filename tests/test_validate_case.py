from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI = REPO_ROOT / "scripts" / "validate-case.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "cases"


def run_validate(case_dir: Path, mode: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), str(case_dir), "--mode", mode],
        capture_output=True,
        text=True,
        check=False,
    )


class ValidateCaseTests(unittest.TestCase):
    def test_strict_mode_accepts_public_fixtures(self) -> None:
        for fixture in ("pattern1-multi-agent", "pattern2-basic"):
            with self.subTest(fixture=fixture):
                result = run_validate(FIXTURES / fixture, "strict")
                self.assertEqual(result.returncode, 0, msg=result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report["errors"], [])

    def test_missing_source_citation_is_error_only_in_strict_exit_code(self) -> None:
        event = {
            "id": "evt_001",
            "ts": "2026-04-24T00:00:00Z",
            "agent": "legal-research-agent",
            "type": "source_graded",
            "data": {
                "agent_id": "legal-research-agent",
                "source": "민법",
                "grade": "A",
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory)
            (case_dir / "events.jsonl").write_text(
                json.dumps(event, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            warn_result = run_validate(case_dir, "warn")
            strict_result = run_validate(case_dir, "strict")

        self.assertEqual(warn_result.returncode, 0, msg=warn_result.stderr)
        self.assertEqual(strict_result.returncode, 1)
        self.assertIn("missing citation", strict_result.stderr)

    def test_second_review_agent_meta_uses_review_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory)
            event = {
                "id": "evt_001",
                "ts": "2026-04-24T00:00:00Z",
                "agent": "second-review-agent",
                "type": "review_completed",
                "data": {},
            }
            (case_dir / "events.jsonl").write_text(
                json.dumps(event, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            (case_dir / "second-review-agent-meta.json").write_text(
                json.dumps(
                    {
                        "approval": "approved",
                        "comments": [],
                        "summary": "review ok",
                        "citation_verification": [],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            result = run_validate(case_dir, "strict")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["errors"], [])

    def test_duplicate_evt_final_is_an_error_but_missing_ids_do_not_collide(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory)
            events = [
                {"ts": "2026-04-24T00:00:00Z", "agent": "a", "type": "noop", "data": {}},
                {"ts": "2026-04-24T00:00:01Z", "agent": "b", "type": "noop", "data": {}},
                {
                    "id": "evt_final",
                    "ts": "2026-04-24T00:00:02Z",
                    "agent": "orchestrator",
                    "type": "final_output",
                    "data": {},
                },
                {
                    "id": "evt_final",
                    "ts": "2026-04-24T00:00:03Z",
                    "agent": "orchestrator",
                    "type": "final_output",
                    "data": {},
                },
            ]
            (case_dir / "events.jsonl").write_text(
                "\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n",
                encoding="utf-8",
            )

            result = run_validate(case_dir, "strict")

        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate event id evt_final", result.stderr)
        self.assertNotIn("duplicate event id ", result.stderr.replace("duplicate event id evt_final", ""))

    def test_review_meta_without_citation_verification_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory)
            event = {
                "id": "evt_001",
                "ts": "2026-07-12T00:00:00Z",
                "agent": "second-review-agent",
                "type": "review_completed",
                "data": {},
            }
            (case_dir / "events.jsonl").write_text(
                json.dumps(event, ensure_ascii=False) + "\n", encoding="utf-8",
            )
            (case_dir / "review-meta.json").write_text(
                json.dumps(
                    {"approval": "approved", "comments": [], "summary": "s"},
                    ensure_ascii=False,
                ) + "\n",
                encoding="utf-8",
            )

            result = run_validate(case_dir, "strict")

        self.assertEqual(result.returncode, 1)
        self.assertIn("missing citation_verification", result.stderr)

    def test_meta_mode_valid_agent_meta_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            meta = Path(directory) / "legal-research-agent-meta.json"
            meta.write_text(
                json.dumps(
                    {
                        "summary": "s",
                        "key_findings": [],
                        "sources": [{"title": "t", "grade": "A", "citation": "c"}],
                        "error": None,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(CLI), "--meta", str(meta)],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_meta_mode_invalid_grade_exits_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            meta = Path(directory) / "legal-research-agent-meta.json"
            meta.write_text(
                json.dumps(
                    {
                        "summary": "s",
                        "key_findings": [],
                        "sources": [{"title": "t", "grade": "Z", "citation": "c"}],
                        "error": None,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(CLI), "--meta", str(meta)],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid grade", result.stderr)


if __name__ == "__main__":
    unittest.main()
