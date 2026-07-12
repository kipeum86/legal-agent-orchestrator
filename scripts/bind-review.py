#!/usr/bin/env python3
"""Bind the current review verdict to the exact reviewed file contents.

Run immediately after second-review-agent completes. Writes review-binding.json
(control-plane artifact, written by the orchestrator, never by a subagent) and
logs a review_bound event. The release gate refuses to finalize when the bound
hashes no longer match the files on disk.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib.events import append_event, utc_now  # noqa: E402
from scripts.lib.review_gate import (  # noqa: E402
    BINDABLE_DELIVERABLES,
    load_review_meta,
    normalize_approval,
    sha256_file,
)


def bind_review(case_dir: Path, *, log_event: bool = True) -> tuple[int, dict]:
    review_meta, review_path = load_review_meta(case_dir)
    if not isinstance(review_meta, dict) or review_path is None:
        return 2, {"status": "error", "reason": "missing_review_meta"}

    reviewed: dict[str, str] = {}
    for name in BINDABLE_DELIVERABLES:
        digest = sha256_file(case_dir / name)
        if digest:
            reviewed[name] = digest
    if not reviewed:
        return 2, {"status": "error", "reason": "no_reviewable_deliverable"}

    payload = {
        "case_id": case_dir.name,
        "review_meta": review_path.name,
        "review_meta_sha256": sha256_file(review_path),
        "approval": normalize_approval(review_meta.get("approval")),
        "reviewed": reviewed,
        "bound_at": utc_now(),
    }
    (case_dir / "review-binding.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    if log_event:
        append_event(
            case_dir / "events.jsonl",
            agent="orchestrator",
            event_type="review_bound",
            data={
                "review_meta": review_path.name,
                "approval": payload["approval"],
                "files": sorted(reviewed),
            },
        )
    return 0, {"status": "bound", **payload}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bind review verdict to reviewed file hashes.")
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("--no-event", action="store_true", help="Skip review_bound event (fixtures/tests).")
    args = parser.parse_args(argv)
    code, report = bind_review(args.case_dir, log_event=not args.no_event)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
