from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FINALIZE_CLI = REPO_ROOT / "scripts" / "finalize-case.py"
MERGE_CLI = REPO_ROOT / "scripts" / "merge-sources.py"
BIND_CLI = REPO_ROOT / "scripts" / "bind-review.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "cases" / "pattern2-basic"


def strip_final_output(case_dir: Path) -> None:
    events_path = case_dir / "events.jsonl"
    lines = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        payload = json.loads(line)
        if payload.get("type") != "final_output":
            lines.append(line)
    events_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_finalize(case_dir: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = {**os.environ, **(env or {})}
    return subprocess.run(
        [sys.executable, str(FINALIZE_CLI), str(case_dir), *args],
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def run_bind(case_dir: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(BIND_CLI), str(case_dir), "--no-event"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr


class FinalizeCaseTests(unittest.TestCase):
    def _revision_needed_case(self, directory: str) -> Path:
        case_dir = Path(directory) / "case"
        shutil.copytree(FIXTURE, case_dir)
        strip_final_output(case_dir)
        review_meta = json.loads((case_dir / "review-meta.json").read_text(encoding="utf-8"))
        review_meta["approval"] = "revision_needed"
        (case_dir / "review-meta.json").write_text(
            json.dumps(review_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
        run_bind(case_dir)
        return case_dir

    def test_allow_unapproved_requires_override_reason(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = self._revision_needed_case(directory)
            result = run_finalize(
                case_dir, "--allow-unapproved",
                env={"LEGAL_ORCHESTRATOR_ALLOW_UNAPPROVED": "1"},
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--override-reason", result.stderr)

    def test_allow_unapproved_requires_env_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = self._revision_needed_case(directory)
            env = {k: v for k, v in os.environ.items() if k != "LEGAL_ORCHESTRATOR_ALLOW_UNAPPROVED"}
            result = subprocess.run(
                [sys.executable, str(FINALIZE_CLI), str(case_dir),
                 "--allow-unapproved", "--override-reason", "사용자 지시"],
                capture_output=True, text=True, check=False, env=env,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("LEGAL_ORCHESTRATOR_ALLOW_UNAPPROVED", result.stderr)

    def test_allow_unapproved_with_guardrails_logs_gate_override(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = self._revision_needed_case(directory)
            result = run_finalize(
                case_dir, "--allow-unapproved", "--override-reason", "사용자 명시 지시",
                env={"LEGAL_ORCHESTRATOR_ALLOW_UNAPPROVED": "1"},
            )
            events = [
                json.loads(line)
                for line in (case_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        overrides = [e for e in events if e.get("type") == "gate_override"]
        self.assertEqual(len(overrides), 1)
        self.assertEqual(overrides[0]["data"]["reason_text"], "사용자 명시 지시")
        final = [e for e in events if e.get("type") == "final_output"]
        self.assertEqual(final[0]["data"]["status"], "not_approved")

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
            run_bind(case_dir)

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
            run_bind(case_dir)

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
            run_bind(case_dir)

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

    def test_check_only_revision_needed_does_not_log_abort_event(self) -> None:
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
            run_bind(case_dir)

            result = run_finalize(case_dir, "--check-only")
            events = [
                json.loads(line)
                for line in (case_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(result.returncode, 3)
        self.assertFalse(any(event.get("type") == "pipeline_aborted" for event in events))
        report = json.loads(result.stdout)
        self.assertIsNone(report["event"])

    def test_corrupt_docx_is_not_selected_as_primary_deliverable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            shutil.copytree(FIXTURE, case_dir)
            strip_final_output(case_dir)
            (case_dir / "opinion.docx").write_bytes(b"not-a-zip")
            (case_dir / "opinion.md").write_text("# Opinion\n", encoding="utf-8")
            run_bind(case_dir)

            result = run_finalize(case_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        report = json.loads(result.stdout)
        final_output = report["event"]["data"]
        self.assertTrue(final_output["primary_deliverable"].endswith("opinion.md"))
        self.assertFalse(any(path.endswith("opinion.docx") for path in final_output["deliverables"]))

    def test_legal_writing_agent_meta_can_supply_summary_and_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            shutil.copytree(FIXTURE, case_dir)
            strip_final_output(case_dir)
            review_meta = json.loads((case_dir / "review-meta.json").read_text(encoding="utf-8"))
            review_meta["summary"] = ""
            (case_dir / "review-meta.json").write_text(
                json.dumps(review_meta, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (case_dir / "writing-meta.json").unlink()
            (case_dir / "legal-writing-agent-meta.json").write_text(
                json.dumps(
                    {"summary": "legacy writing summary", "pattern": "pattern_3", "sources": []},
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            run_bind(case_dir)

            result = run_finalize(case_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        final_output = json.loads(result.stdout)["event"]["data"]
        self.assertEqual(final_output["summary"], "legacy writing summary")
        self.assertEqual(final_output["pattern"], "pattern_3")


if __name__ == "__main__":
    unittest.main()
