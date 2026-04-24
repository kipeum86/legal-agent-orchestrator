from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI = REPO_ROOT / "scripts" / "acceptance-check.py"


class AcceptanceCheckTests(unittest.TestCase):
    def test_acceptance_check_passes_all_criteria_as_json(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CLI), "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["passed"])
        self.assertEqual(payload["total"], 12)
        self.assertEqual(payload["passed_count"], 12)

    def test_acceptance_check_writes_markdown_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "acceptance.md"
            result = subprocess.run(
                [sys.executable, str(CLI), "--write", str(report)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            text = report.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Status: PASS (12/12 criteria)", text)
        self.assertIn("Pattern 3 transcript", text)
        self.assertIn("MCP pinning", text)


if __name__ == "__main__":
    unittest.main()
