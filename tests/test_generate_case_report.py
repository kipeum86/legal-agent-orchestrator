from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_CLI = REPO_ROOT / "scripts" / "generate-case-report.py"
MERGE_CLI = REPO_ROOT / "scripts" / "merge-sources.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "cases" / "pattern1-multi-agent"


class GenerateCaseReportTests(unittest.TestCase):
    def test_report_discovers_specialized_agent_meta_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            shutil.copytree(FIXTURE, case_dir)
            merge_result = subprocess.run(
                [sys.executable, str(MERGE_CLI), str(case_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(merge_result.returncode, 0, msg=merge_result.stderr)

            report_result = subprocess.run(
                [sys.executable, str(REPORT_CLI), str(case_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(report_result.returncode, 0, msg=report_result.stderr)
            report = (case_dir / "case-report.md").read_text(encoding="utf-8")

        self.assertIn("개인정보보호법 스페셜리스트", report)
        self.assertIn("GDPR 스페셜리스트", report)
        self.assertIn("개인정보 보호법", report)
        self.assertIn("제28조의8", report)
        self.assertIn("Article 28", report)


if __name__ == "__main__":
    unittest.main()
