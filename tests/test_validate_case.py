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


if __name__ == "__main__":
    unittest.main()
