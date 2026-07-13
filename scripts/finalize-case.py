#!/usr/bin/env python3
"""Gate and write final_output for an orchestrator case directory."""
from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib.events import append_event  # noqa: E402
from scripts.lib.io_utils import parse_jsonl, read_json  # noqa: E402
from scripts.lib.review_gate import evaluate_gate  # noqa: E402


def load_writing_meta(case_dir: Path) -> dict[str, Any] | None:
    candidates = [case_dir / "writing-meta.json", case_dir / "legal-writing-agent-meta.json"]
    candidates.extend(path for path in sorted(case_dir.glob("*writing*-meta.json")) if path not in candidates)
    for path in candidates:
        payload = read_json(path)
        if isinstance(payload, dict):
            return payload
    return None


def load_sources_payload(case_dir: Path) -> dict[str, Any]:
    payload = read_json(case_dir / "sources.json")
    return payload if isinstance(payload, dict) else {}


def existing_final_output(case_dir: Path) -> dict[str, Any] | None:
    for event in reversed(parse_jsonl(case_dir / "events.jsonl")):
        if event.get("type") == "final_output":
            data = event.get("data")
            return data if isinstance(data, dict) else {}
    return None


def first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def derive_summary(case_dir: Path, review_meta: dict[str, Any], explicit_summary: str | None) -> str:
    if explicit_summary:
        return explicit_summary
    writing_meta = load_writing_meta(case_dir)
    return (
        first_string(
            review_meta.get("summary"),
            writing_meta.get("summary") if isinstance(writing_meta, dict) else None,
        )
        or "Final output completed."
    )


def derive_pattern(case_dir: Path) -> str | None:
    writing_meta = load_writing_meta(case_dir)
    if isinstance(writing_meta, dict):
        pattern = first_string(writing_meta.get("pattern"))
        if pattern:
            return pattern
    for event in reversed(parse_jsonl(case_dir / "events.jsonl")):
        if event.get("type") != "case_classified":
            continue
        data = event.get("data")
        if isinstance(data, dict):
            pattern = first_string(data.get("pattern"))
            if pattern:
                return pattern
    return None


def detect_deliverables(case_dir: Path) -> list[Path]:
    candidates = [
        "opinion.docx",
        "opinion.md",
        "debate-opinion.docx",
        "debate-opinion.md",
        "debate-transcript.docx",
        "debate-transcript.md",
        "case-report.md",
        "sources.json",
    ]
    deliverables: list[Path] = []
    for name in candidates:
        path = case_dir / name
        if not path.exists():
            continue
        if path.suffix == ".docx" and not zipfile.is_zipfile(path):
            continue
        deliverables.append(path)
    return deliverables


PRIMARY_DELIVERABLE_BASENAMES = {
    "opinion.docx",
    "opinion.md",
    "debate-opinion.docx",
    "debate-opinion.md",
}


def choose_primary(case_dir: Path, explicit_path: str | None) -> Path | None:
    if explicit_path:
        path = Path(explicit_path).expanduser()
        path = path if path.is_absolute() else (case_dir / path)
        resolved = path.resolve()
        if (
            resolved.parent != case_dir.resolve()
            or resolved.name not in PRIMARY_DELIVERABLE_BASENAMES
            or not resolved.exists()
            or (resolved.suffix == ".docx" and not zipfile.is_zipfile(resolved))
        ):
            raise ValueError("invalid_primary_deliverable")
        return resolved
    for path in detect_deliverables(case_dir):
        if path.name in {"sources.json", "case-report.md", "debate-transcript.md", "debate-transcript.docx"}:
            continue
        return path
    return None


def append_abort_event(case_dir: Path, reason: str, approval: str, review_path: Path | None) -> dict[str, Any]:
    data = {
        "reason": reason,
        "last_completed_step": "second-review-agent",
        "approval": approval,
        "review_meta": review_path.name if review_path else None,
        "recovery": "request_revision_cycle_before_final_output",
    }
    return append_event(
        case_dir / "events.jsonl",
        agent="orchestrator",
        event_type="pipeline_aborted",
        data={key: value for key, value in data.items() if value is not None},
    )


def build_final_data(
    case_dir: Path,
    review_meta: dict[str, Any],
    approval: str,
    summary: str,
    primary: Path | None,
) -> dict[str, Any]:
    sources = load_sources_payload(case_dir)
    deliverables = [str(path) for path in detect_deliverables(case_dir)]
    data: dict[str, Any] = {
        "case_id": case_dir.name,
        "final_approval": approval,
        "summary": summary,
        "total_sources": int(sources.get("total_sources", 0) or 0),
        "grade_distribution": sources.get("grade_distribution", {}),
        "deliverables": deliverables,
    }
    if primary is not None:
        data["primary_deliverable"] = str(primary)
        data["file_path"] = str(primary)
        if primary.suffix:
            data["format"] = primary.suffix.lstrip(".")
    pattern = derive_pattern(case_dir)
    if pattern:
        data["pattern"] = pattern
    comments = review_meta.get("comments")
    if isinstance(comments, list):
        data["review_comments_count"] = len(comments)
    return data


def finalize_case(
    case_dir: Path,
    *,
    check_only: bool = False,
    summary: str | None = None,
    primary_deliverable: str | None = None,
    allow_unapproved: bool = False,
    override_reason: str | None = None,
) -> tuple[int, dict[str, Any]]:
    gate = evaluate_gate(case_dir)
    review_meta = gate.review_meta if isinstance(gate.review_meta, dict) else {}
    approval = gate.approval

    if not gate.ok:
        overridable = gate.exit_code == 3 and allow_unapproved
        if not overridable:
            event = None if check_only else append_abort_event(case_dir, gate.reason, approval, gate.review_path)
            report: dict[str, Any] = {"status": "aborted", "reason": gate.reason, "event": event}
            if gate.reason != "missing_review_meta":
                report["approval"] = approval
            return gate.exit_code, report

    if primary_deliverable and Path(primary_deliverable).name.lower().endswith(".draft.docx"):
        return 2, {
            "status": "aborted",
            "reason": "draft_primary_deliverable",
            "approval": approval,
        }

    try:
        primary = choose_primary(case_dir, primary_deliverable)
    except ValueError:
        return 2, {
            "status": "aborted",
            "reason": "invalid_primary_deliverable",
            "approval": approval,
        }
    final_data = build_final_data(
        case_dir,
        review_meta,
        approval,
        derive_summary(case_dir, review_meta, summary),
        primary,
    )
    if not gate.ok and allow_unapproved:
        final_data["status"] = "not_approved"
        final_data["gate_reason"] = gate.reason

    if check_only:
        return 0, {"status": "ready", "approval": approval, "would_write": final_data}

    existing = existing_final_output(case_dir)
    if existing is not None:
        return 0, {"status": "already_finalized", "approval": approval, "final_output": existing}

    if not gate.ok and allow_unapproved:
        append_event(
            case_dir / "events.jsonl",
            agent="orchestrator",
            event_type="gate_override",
            data={
                "override": "allow_unapproved",
                "reason_text": override_reason or "",
                "approval": approval,
                "gate_reason": gate.reason,
            },
        )

    event = append_event(
        case_dir / "events.jsonl",
        agent="orchestrator",
        event_type="final_output",
        data=final_data,
        final=True,
    )
    return 0, {"status": "finalized", "approval": approval, "event": event}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gate review approval and write final_output.")
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--summary", default=None)
    parser.add_argument("--primary-deliverable", default=None)
    parser.add_argument(
        "--allow-unapproved",
        action="store_true",
        help="Write final_output with status=not_approved even when review requires revision.",
    )
    parser.add_argument("--override-reason", default=None,
                        help="Required with --allow-unapproved: why the gate is being bypassed.")
    args = parser.parse_args(argv)

    if args.allow_unapproved:
        if not (args.override_reason and args.override_reason.strip()):
            print("finalize-case: --allow-unapproved requires --override-reason", file=sys.stderr)
            return 2
        if os.environ.get("LEGAL_ORCHESTRATOR_ALLOW_UNAPPROVED") != "1":
            print(
                "finalize-case: --allow-unapproved requires LEGAL_ORCHESTRATOR_ALLOW_UNAPPROVED=1 "
                "(set it only on explicit user instruction)",
                file=sys.stderr,
            )
            return 2

    code, report = finalize_case(
        args.case_dir,
        check_only=args.check_only,
        summary=args.summary,
        primary_deliverable=args.primary_deliverable,
        allow_unapproved=args.allow_unapproved,
        override_reason=args.override_reason,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
