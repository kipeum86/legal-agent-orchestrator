from __future__ import annotations

import importlib.util
import json
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

REPORT_SPEC = importlib.util.spec_from_file_location("generate_case_report", REPORT_CLI)
assert REPORT_SPEC is not None
REPORT_MODULE = importlib.util.module_from_spec(REPORT_SPEC)
assert REPORT_SPEC.loader is not None
REPORT_SPEC.loader.exec_module(REPORT_MODULE)


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

    def test_approved_with_revisions_is_rendered_as_pending_rereview(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            shutil.copytree(FIXTURE, case_dir)
            review_path = case_dir / "review-meta.json"
            review_meta = json.loads(review_path.read_text(encoding="utf-8"))
            review_meta["approval"] = "approved_with_revisions"
            review_path.write_text(
                json.dumps(review_meta, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            report_result = subprocess.run(
                [sys.executable, str(REPORT_CLI), str(case_dir)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(report_result.returncode, 0, msg=report_result.stderr)
            report = (case_dir / "case-report.md").read_text(encoding="utf-8")

        self.assertIn("- 상태: ⏸ 수정 후 재리뷰 대기", report)
        self.assertIn("- 판정: ⏸ 수정 후 재리뷰 대기", report)
        self.assertNotIn("✓ 수정 후 승인", report)

    def test_case_validation_warnings_are_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            shutil.copytree(FIXTURE, case_dir)
            warning = (
                "legal-research-agent-meta.json: sources[1] jurisdiction_mismatch: "
                "JP not in classification ['KR']"
            )
            (case_dir / "case-validation.json").write_text(
                json.dumps({"errors": [], "warnings": [warning]}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            report_result = subprocess.run(
                [sys.executable, str(REPORT_CLI), str(case_dir)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(report_result.returncode, 0, msg=report_result.stderr)
            report = (case_dir / "case-report.md").read_text(encoding="utf-8")

        self.assertIn("## 검증 경고", report)
        self.assertIn("jurisdiction_mismatch", report)
        self.assertIn("JP not in classification", report)

    def test_meta_bundle_skips_debate_round_meta_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            case_dir.mkdir()
            (case_dir / "debate-round-1-legal-research-agent-meta.json").write_text(
                json.dumps(
                    {
                        "round": 1,
                        "summary": "debate round summary must not become primary research",
                        "key_findings": ["debate-only finding"],
                        "sources": [{"title": "Debate source", "grade": "A", "citation": "R1"}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (case_dir / "writing-meta.json").write_text(
                json.dumps({"summary": "writing summary", "sources": []}, ensure_ascii=False),
                encoding="utf-8",
            )

            bundle = REPORT_MODULE.load_meta_bundle(case_dir)

        self.assertNotIn("debate-round-1-legal-research-agent", bundle)
        self.assertNotIn("legal-research-agent", bundle)
        self.assertIsNone(REPORT_MODULE.select_primary_research_meta(bundle))

    def test_infer_pattern_tolerates_null_event_data(self) -> None:
        pattern = REPORT_MODULE.infer_pattern(
            [
                {
                    "id": "evt_001",
                    "type": "case_classified",
                    "data": None,
                }
            ]
        )

        self.assertEqual(pattern, 1)

    def test_transform_opinion_markdown_ignores_headings_inside_code_fences(self) -> None:
        transformed = REPORT_MODULE.transform_opinion_markdown(
            "# Opinion\n\n```python\n# comment heading\n```\n\n## Real Section"
        )

        self.assertNotIn("# Opinion", transformed)
        self.assertIn("```python\n# comment heading\n```", transformed)
        self.assertIn("### Real Section", transformed)

    def test_rejects_project_relative_case_dir_outside_allowed_outputs(self) -> None:
        result = subprocess.run(
            [sys.executable, str(REPORT_CLI), "schemas/leak"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("output/ or samples", result.stderr)

    def test_missing_events_file_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            case_dir.mkdir()
            result = subprocess.run(
                [sys.executable, str(REPORT_CLI), str(case_dir)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("events.jsonl", result.stderr)

    def test_report_redacts_event_pii_and_avoids_unknown_event_dump(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            case_dir.mkdir()
            events = [
                {
                    "id": "evt_001",
                    "ts": "2026-04-24T00:00:00Z",
                    "agent": "orchestrator",
                    "type": "case_received",
                    "data": {"query": "Contact user@example.com"},
                },
                {
                    "id": "evt_002",
                    "ts": "2026-04-24T00:00:01Z",
                    "agent": "orchestrator",
                    "type": "user_prompt",
                    "data": {"question": "주민번호 900101-1234567 확인 필요"},
                },
                {
                    "id": "evt_003",
                    "ts": "2026-04-24T00:00:02Z",
                    "agent": "orchestrator",
                    "type": "unknown_event",
                    "data": {"token": "sk-abc123def456ghi78900", "note": "internal"},
                },
            ]
            (case_dir / "events.jsonl").write_text(
                "\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(REPORT_CLI), str(case_dir)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            report = (case_dir / "case-report.md").read_text(encoding="utf-8")

        self.assertNotIn("user@example.com", report)
        self.assertNotIn("900101-1234567", report)
        self.assertNotIn("sk-abc123def456ghi78900", report)
        self.assertIn("[REDACTED:email]", report)
        self.assertIn("[REDACTED:rrn]", report)
        self.assertIn("세부 필드는 내부 이벤트 로그에 보관됩니다", report)


if __name__ == "__main__":
    unittest.main()
