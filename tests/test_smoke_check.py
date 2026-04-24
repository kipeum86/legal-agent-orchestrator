from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SMOKE_CLI = REPO_ROOT / "scripts" / "smoke-check.py"


class SmokeCheckTests(unittest.TestCase):
    def test_smoke_check_exits_zero_and_leaves_fixture_clean(self) -> None:
        fixture_report = REPO_ROOT / "tests" / "fixtures" / "cases" / "pattern2-basic" / "case-report.md"
        self.assertFalse(fixture_report.exists(), "fixture case-report.md should not be pre-generated")

        result = subprocess.run(
            [sys.executable, str(SMOKE_CLI)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("[smoke] OK", result.stdout)
        self.assertFalse(fixture_report.exists())

    def test_contributing_documents_minimum_smoke_commands(self) -> None:
        text = (REPO_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertIn("python3 -m unittest", text)
        self.assertIn("python3 scripts/sanitize-check.py --self-test", text)
        self.assertIn("python3 scripts/generate-case-report.py tests/fixtures/cases/pattern2-basic", text)


if __name__ == "__main__":
    unittest.main()
