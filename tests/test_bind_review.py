from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BIND_CLI = REPO_ROOT / "scripts" / "bind-review.py"


def make_case(root: Path) -> Path:
    case_dir = root / "case"
    case_dir.mkdir()
    (case_dir / "events.jsonl").write_text("", encoding="utf-8")
    (case_dir / "opinion.md").write_text("# 의견서\n본문.\n", encoding="utf-8")
    (case_dir / "review-meta.json").write_text(
        json.dumps({"approval": "approved", "summary": "s", "comments": [], "error": None},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return case_dir


def run_bind(case_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BIND_CLI), str(case_dir), *args],
        capture_output=True, text=True, check=False,
    )


class BindReviewTests(unittest.TestCase):
    def test_writes_binding_with_hashes_and_logs_event(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = make_case(Path(directory))
            result = run_bind(case_dir)

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            binding = json.loads((case_dir / "review-binding.json").read_text(encoding="utf-8"))
            events = [json.loads(line) for line in
                      (case_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(binding["approval"], "approved")
        self.assertEqual(binding["review_meta"], "review-meta.json")
        self.assertEqual(len(binding["reviewed"]["opinion.md"]), 64)
        self.assertEqual(len(binding["review_meta_sha256"]), 64)
        bound = [e for e in events if e.get("type") == "review_bound"]
        self.assertEqual(len(bound), 1)
        self.assertEqual(bound[0]["data"]["files"], ["opinion.md"])

    def test_no_event_flag_skips_event(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = make_case(Path(directory))
            result = run_bind(case_dir, "--no-event")
            events_text = (case_dir / "events.jsonl").read_text(encoding="utf-8")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("review_bound", events_text)

    def test_fails_without_review_meta(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            case_dir.mkdir()
            (case_dir / "opinion.md").write_text("x\n", encoding="utf-8")
            result = run_bind(case_dir)
        self.assertEqual(result.returncode, 2)

    def test_fails_without_any_deliverable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = make_case(Path(directory))
            (case_dir / "opinion.md").unlink()
            result = run_bind(case_dir)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
