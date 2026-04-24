#!/usr/bin/env python3
"""Gate and write final_output for an orchestrator case directory."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

APPROVED_STATUSES = {"approved", "approved_with_revisions"}
BLOCKING_STATUSES = {"revision_needed"}
VALID_STATUSES = APPROVED_STATUSES | BLOCKING_STATUSES


def load_log_event_module():
    module_path = Path(__file__).with_name("log-event.py")
    spec = importlib.util.spec_from_file_location("log_event", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load log-event module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    events: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def load_review_meta(case_dir: Path) -> tuple[dict[str, Any] | None, Path | None]:
    candidates = [case_dir / "review-meta.json", case_dir / "second-review-agent-meta.json"]
    candidates.extend(path for path in sorted(case_dir.glob("*review*-meta.json")) if path not in candidates)
    for path in candidates:
        payload = read_json(path)
        if isinstance(payload, dict):
            return payload, path
    return None, None


def normalize_approval(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


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
    writing_meta = read_json(case_dir / "writing-meta.json")
    return (
        first_string(
            review_meta.get("summary"),
            writing_meta.get("summary") if isinstance(writing_meta, dict) else None,
        )
        or "Final output completed."
    )


def derive_pattern(case_dir: Path) -> str | None:
    writing_meta = read_json(case_dir / "writing-meta.json")
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
    return [case_dir / name for name in candidates if (case_dir / name).exists()]


def choose_primary(case_dir: Path, explicit_path: str | None) -> Path | None:
    if explicit_path:
        path = Path(explicit_path).expanduser()
        return path if path.is_absolute() else (case_dir / path)
    for path in detect_deliverables(case_dir):
        if path.name in {"sources.json", "case-report.md", "debate-transcript.md", "debate-transcript.docx"}:
            continue
        return path
    return None


def append_abort_event(case_dir: Path, reason: str, approval: str, review_path: Path | None) -> dict[str, Any]:
    log_event = load_log_event_module()
    data = {
        "reason": reason,
        "last_completed_step": "second-review-agent",
        "approval": approval,
        "review_meta": review_path.name if review_path else None,
        "recovery": "request_revision_cycle_before_final_output",
    }
    return log_event.append_event(
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
    if approval == "approved_with_revisions":
        data["revision_note"] = "review approved with revisions; confirm revisions are reflected before client delivery"
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
) -> tuple[int, dict[str, Any]]:
    review_meta, review_path = load_review_meta(case_dir)
    if not isinstance(review_meta, dict):
        event = append_abort_event(case_dir, "missing_review_meta", "missing", review_path)
        return 2, {"status": "aborted", "reason": "missing_review_meta", "event": event}

    approval = normalize_approval(review_meta.get("approval"))
    if approval not in VALID_STATUSES:
        event = append_abort_event(case_dir, "invalid_review_approval", approval or "missing", review_path)
        return 2, {"status": "aborted", "reason": "invalid_review_approval", "approval": approval, "event": event}

    if approval in BLOCKING_STATUSES and not allow_unapproved:
        event = append_abort_event(case_dir, "review_revision_needed", approval, review_path)
        return 3, {"status": "aborted", "reason": "review_revision_needed", "approval": approval, "event": event}

    primary = choose_primary(case_dir, primary_deliverable)
    final_data = build_final_data(
        case_dir,
        review_meta,
        approval,
        derive_summary(case_dir, review_meta, summary),
        primary,
    )
    if approval in BLOCKING_STATUSES and allow_unapproved:
        final_data["status"] = "not_approved"

    if check_only:
        return 0, {"status": "ready", "approval": approval, "would_write": final_data}

    existing = existing_final_output(case_dir)
    if existing is not None:
        return 0, {"status": "already_finalized", "approval": approval, "final_output": existing}

    log_event = load_log_event_module()
    event = log_event.append_event(
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
    args = parser.parse_args(argv)

    code, report = finalize_case(
        args.case_dir,
        check_only=args.check_only,
        summary=args.summary,
        primary_deliverable=args.primary_deliverable,
        allow_unapproved=args.allow_unapproved,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
