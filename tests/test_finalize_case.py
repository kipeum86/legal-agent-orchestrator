from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FINALIZE_CLI = REPO_ROOT / "scripts" / "finalize-case.py"
MERGE_CLI = REPO_ROOT / "scripts" / "merge-sources.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "cases" / "pattern2-basic"


def strip_final_output(case_dir: Path) -> None:
    events_path = case_dir / "events.jsonl"
    lines = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        payload = json.loads(line)
        if payload.get("type") != "final_output":
            lines.append(line)
    events_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_finalize(case_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(FINALIZE_CLI), str(case_dir), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class FinalizeCaseTests(unittest.TestCase):
    def test_approved_review_writes_final_output_with_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            shutil.copytree(FIXTURE, case_dir)
            strip_final_output(case_dir)
            subprocess.run(
                [sys.executable, str(MERGE_CLI), str(case_dir)],
                capture_output=True,
                text=True,
                check=True,
            )

            result = run_finalize(case_dir, "--summary", "승인된 최종 요약")

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            events = [
                json.loads(line)
                for line in (case_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        final_events = [event for event in events if event.get("type") == "final_output"]
        self.assertEqual(len(final_events), 1)
        final_data = final_events[0]["data"]
        self.assertEqual(final_events[0]["id"], "evt_final")
        self.assertEqual(final_data["final_approval"], "approved")
        self.assertEqual(final_data["total_sources"], 1)
        self.assertEqual(final_data["summary"], "승인된 최종 요약")

    def test_revision_needed_blocks_final_output_and_logs_abort(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            shutil.copytree(FIXTURE, case_dir)
            strip_final_output(case_dir)
            review_meta = json.loads((case_dir / "review-meta.json").read_text(encoding="utf-8"))
            review_meta["approval"] = "revision_needed"
            (case_dir / "review-meta.json").write_text(
                json.dumps(review_meta, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = run_finalize(case_dir)
            events = [
                json.loads(line)
                for line in (case_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(result.returncode, 3)
        self.assertFalse(any(event.get("type") == "final_output" for event in events))
        abort_events = [event for event in events if event.get("type") == "pipeline_aborted"]
        self.assertEqual(len(abort_events), 1)
        self.assertEqual(abort_events[0]["data"]["reason"], "review_revision_needed")

    def test_check_only_does_not_write_final_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            shutil.copytree(FIXTURE, case_dir)
            strip_final_output(case_dir)

            result = run_finalize(case_dir, "--check-only")
            events = [
                json.loads(line)
                for line in (case_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertFalse(any(event.get("type") == "final_output" for event in events))
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "ready")


if __name__ == "__main__":
    unittest.main()
