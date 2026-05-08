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

        self.assertIn("데이터보호 스페셜리스트", report)
        self.assertIn("법률 리서치 스페셜리스트", report)
        self.assertIn("개인정보 보호법", report)
        self.assertIn("제28조의8", report)
        self.assertIn("Article 28", report)
        self.assertIn("Article 25", report)

    def test_report_generates_when_final_output_event_is_absent(self) -> None:
        # Regression: deliver-output.md generates case-report.md BEFORE
        # finalize-case writes the `final_output` event. Earlier the script
        # crashed in that ordering with `'NoneType' object has no attribute
        # 'get'` because final_output_event was None. Verify the script now
        # tolerates a missing final_output event.
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            shutil.copytree(FIXTURE, case_dir)

            events_path = case_dir / "events.jsonl"
            kept_lines = [
                line
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and '"type":"final_output"' not in line
            ]
            events_path.write_text("\n".join(kept_lines) + "\n", encoding="utf-8")

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
            self.assertTrue((case_dir / "case-report.md").exists())


if __name__ == "__main__":
    unittest.main()
