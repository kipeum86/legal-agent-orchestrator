from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.review_gate import evaluate_gate  # noqa: E402


def write_review_meta(case_dir: Path, approval: str) -> None:
    (case_dir / "review-meta.json").write_text(
        json.dumps({"approval": approval, "summary": "s", "comments": [], "error": None},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def append_event_line(case_dir: Path, event_type: str, data: dict) -> None:
    line = json.dumps(
        {"id": "evt_099", "ts": "2026-07-12T00:00:00Z", "agent": "orchestrator",
         "type": event_type, "data": data},
        ensure_ascii=False,
    )
    with (case_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


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
            gate = evaluate_gate(case_dir)
        self.assertTrue(gate.ok)
        self.assertEqual(gate.exit_code, 0)
        self.assertIsNone(gate.reason)
        self.assertEqual(gate.approval, "approved")

    def test_verbatim_failed_blocks(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved")
            append_event_line(case_dir, "verbatim_verified", {"verifier": "orchestrator", "passed": False})
            gate = evaluate_gate(case_dir)
        self.assertEqual((gate.ok, gate.exit_code, gate.reason), (False, 3, "verbatim_verification_failed"))

    def test_verbatim_passed_true_allows(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved")
            append_event_line(case_dir, "verbatim_verified", {"verifier": "orchestrator", "passed": True})
            gate = evaluate_gate(case_dir)
        self.assertTrue(gate.ok)

    def test_verbatim_legacy_event_without_passed_allows(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved")
            append_event_line(case_dir, "verbatim_verified", {"verifier": "orchestrator", "critical_pass": 2})
            gate = evaluate_gate(case_dir)
        self.assertTrue(gate.ok)
        self.assertEqual(gate.detail.get("verbatim"), "legacy_event_without_passed")

    def test_latest_verbatim_event_wins(self) -> None:
        holder, case_dir = self.make_case()
        with holder:
            write_review_meta(case_dir, "approved")
            append_event_line(case_dir, "verbatim_verified", {"passed": False})
            append_event_line(case_dir, "verbatim_verified", {"passed": True})
            gate = evaluate_gate(case_dir)
        self.assertTrue(gate.ok)


if __name__ == "__main__":
    unittest.main()
