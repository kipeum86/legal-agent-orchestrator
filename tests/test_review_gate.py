from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.review_gate import evaluate_gate  # noqa: E402


def write_review_meta(
    case_dir: Path,
    approval: str,
    summary: str = "s",
    citation_verification: list | None = None,
) -> None:
    payload = {
        "approval": approval,
        "summary": summary,
        "comments": [],
        "citation_verification": (
            citation_verification
            if citation_verification is not None
            else [{"citation": "테스트법 제1조", "status": "verified", "method": "primary_db"}]
        ),
        "error": None,
    }
    (case_dir / "review-meta.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )


def append_event_line(case_dir: Path, event_type: str, data: dict) -> None:
    line = json.dumps(
        {"id": "evt_099", "ts": "2026-07-12T00:00:00Z", "agent": "orchestrator",
         "type": event_type, "data": data},
        ensure_ascii=False,
    )
    with (case_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def bind(case_dir: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "bind-review.py"), str(case_dir), "--no-event"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr


class EvaluateGateTests(unittest.TestCase):
    def make_case(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        directory = tempfile.TemporaryDirectory()
        case_dir = Path(directory.name) / "case"
        case_dir.mkdir()
        (case_dir / "events.jsonl").write_text("", encoding="utf-8")
        (case_dir / "opinion.md").write_text("# opinion\n", encoding="utf-8")
        return directory, case_dir

    def test_missing_review_meta_blocks_with_exit_2(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            gate = evaluate_gate(case_dir)
        self.assertFalse(gate.ok)
        self.assertEqual(gate.exit_code, 2)
        self.assertEqual(gate.reason, "missing_review_meta")

    def test_invalid_approval_blocks_with_exit_2(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "maybe")
            gate = evaluate_gate(case_dir)
        self.assertEqual((gate.ok, gate.exit_code, gate.reason), (False, 2, "invalid_review_approval"))

    def test_revision_needed_blocks_with_exit_3(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "revision_needed")
            gate = evaluate_gate(case_dir)
        self.assertEqual((gate.ok, gate.exit_code, gate.reason), (False, 3, "review_revision_needed"))

    def test_approved_passes(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved")
            bind(case_dir)
            gate = evaluate_gate(case_dir)
        self.assertTrue(gate.ok)
        self.assertEqual(gate.exit_code, 0)
        self.assertIsNone(gate.reason)
        self.assertEqual(gate.approval, "approved")

    def test_verbatim_failed_blocks(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved")
            bind(case_dir)
            append_event_line(case_dir, "verbatim_verified", {"verifier": "orchestrator", "passed": False})
            gate = evaluate_gate(case_dir)
        self.assertEqual((gate.ok, gate.exit_code, gate.reason), (False, 3, "verbatim_verification_failed"))

    def test_verbatim_passed_true_allows(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved")
            bind(case_dir)
            append_event_line(case_dir, "verbatim_verified", {"verifier": "orchestrator", "passed": True})
            gate = evaluate_gate(case_dir)
        self.assertTrue(gate.ok)

    def test_verbatim_legacy_event_without_passed_allows(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved")
            bind(case_dir)
            append_event_line(case_dir, "verbatim_verified", {"verifier": "orchestrator", "critical_pass": 2})
            gate = evaluate_gate(case_dir)
        self.assertTrue(gate.ok)
        self.assertEqual(gate.detail.get("verbatim"), "legacy_event_without_passed")

    def test_latest_verbatim_event_wins(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved")
            bind(case_dir)
            append_event_line(case_dir, "verbatim_verified", {"passed": False})
            append_event_line(case_dir, "verbatim_verified", {"passed": True})
            gate = evaluate_gate(case_dir)
        self.assertTrue(gate.ok)

    def test_missing_binding_blocks(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved")
            gate = evaluate_gate(case_dir)
        self.assertEqual((gate.ok, gate.exit_code, gate.reason), (False, 3, "missing_review_binding"))

    def test_editing_opinion_after_bind_blocks(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved")
            bind(case_dir)
            (case_dir / "opinion.md").write_text("# 몰래 수정\n", encoding="utf-8")
            gate = evaluate_gate(case_dir)
        self.assertEqual((gate.ok, gate.reason), (False, "stale_review_binding"))
        self.assertEqual(gate.detail["mismatch"], "opinion.md")

    def test_editing_review_meta_after_bind_blocks(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved")
            bind(case_dir)
            write_review_meta(case_dir, "approved", summary="edited")
            gate = evaluate_gate(case_dir)
        self.assertEqual((gate.ok, gate.reason), (False, "stale_review_binding"))

    def test_approved_with_revisions_blocks_pending_rereview(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved_with_revisions")
            bind(case_dir)
            gate = evaluate_gate(case_dir)
        self.assertEqual((gate.ok, gate.exit_code, gate.reason), (False, 3, "review_revisions_pending"))

    def test_missing_citation_verification_blocks(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved", citation_verification=[])
            payload = json.loads((case_dir / "review-meta.json").read_text(encoding="utf-8"))
            del payload["citation_verification"]
            (case_dir / "review-meta.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            bind(case_dir)
            gate = evaluate_gate(case_dir)
        self.assertEqual((gate.ok, gate.exit_code, gate.reason), (False, 3, "citation_verification_missing"))

    def test_nonexistent_citation_blocks(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved", citation_verification=[
                {"citation": "가공의 법률 제99조", "status": "nonexistent", "method": "primary_db"},
            ])
            bind(case_dir)
            gate = evaluate_gate(case_dir)
        self.assertEqual((gate.ok, gate.reason), (False, "citation_verification_failed"))
        self.assertEqual(gate.detail["citation_counts"]["nonexistent"], 1)

    def test_unverified_citation_blocks(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved", citation_verification=[
                {"citation": "테스트법 제1조", "status": "verified"},
                {"citation": "미확인법 제2조", "status": "unverified"},
            ])
            bind(case_dir)
            gate = evaluate_gate(case_dir)
        self.assertEqual((gate.ok, gate.reason), (False, "citation_verification_failed"))

    def test_verified_and_not_checked_pass(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved", citation_verification=[
                {"citation": "테스트법 제1조", "status": "verified"},
                {"citation": "부수 인용", "status": "not_checked"},
            ])
            bind(case_dir)
            gate = evaluate_gate(case_dir)
        self.assertTrue(gate.ok)


if __name__ == "__main__":
    unittest.main()
