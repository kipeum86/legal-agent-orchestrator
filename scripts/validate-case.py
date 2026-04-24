#!/usr/bin/env python3
"""Validate a legal-agent-orchestrator case directory.

This intentionally uses stdlib checks instead of a JSON Schema dependency so it
can run in fresh Claude Code environments without setup.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

GRADES = {"A", "B", "C", "D"}
REVIEW_APPROVALS = {"approved", "approved_with_revisions", "revision_needed"}
REVIEW_SEVERITIES = {"critical", "major", "minor", "suggestion"}


def read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def parse_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    events: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return [], [f"missing events file: {path.name}"]
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"events.jsonl:{index}: invalid JSON: {exc}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"events.jsonl:{index}: event must be an object")
            continue
        events.append(payload)
    return events, errors


def require_mapping(value: Any, label: str, errors: list[str]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    errors.append(f"{label}: expected object")
    return {}


def validate_events(case_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    events, parse_errors = parse_jsonl(case_dir / "events.jsonl")
    errors.extend(parse_errors)

    seen_ids: set[str] = set()
    for index, event in enumerate(events, start=1):
        label = f"events.jsonl:{index}"
        for key in ("id", "ts", "agent", "type", "data"):
            if key not in event:
                errors.append(f"{label}: missing {key}")
        event_id = str(event.get("id") or "")
        if event_id in seen_ids and event_id != "evt_final":
            errors.append(f"{label}: duplicate event id {event_id}")
        seen_ids.add(event_id)

        data = require_mapping(event.get("data"), f"{label}.data", errors)
        event_type = str(event.get("type") or "")
        if event_type == "source_graded":
            for key in ("agent_id", "source", "grade", "citation"):
                if not str(data.get(key) or "").strip():
                    errors.append(f"{label}: source_graded.data missing {key}")
            grade = str(data.get("grade") or "")
            if grade and grade not in GRADES:
                errors.append(f"{label}: invalid source grade {grade}")

    return errors, warnings


def validate_agent_meta(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    payload = read_json(path)
    if not isinstance(payload, dict):
        return [f"{path.name}: invalid or missing JSON object"], warnings

    for key in ("summary", "key_findings", "sources"):
        if key not in payload:
            errors.append(f"{path.name}: missing {key}")

    summary = payload.get("summary")
    if isinstance(summary, str) and len(summary) > 4000:
        warnings.append(f"{path.name}: summary appears longer than 500 tokens target")

    key_findings = payload.get("key_findings")
    if key_findings is not None and not isinstance(key_findings, list):
        errors.append(f"{path.name}: key_findings must be an array")

    sources = payload.get("sources")
    if sources is not None and not isinstance(sources, list):
        errors.append(f"{path.name}: sources must be an array")
    if isinstance(sources, list):
        for index, source in enumerate(sources, start=1):
            if not isinstance(source, dict):
                errors.append(f"{path.name}: sources[{index}] must be an object")
                continue
            for key in ("title", "grade", "citation"):
                if not str(source.get(key) or "").strip():
                    errors.append(f"{path.name}: sources[{index}] missing {key}")
            grade = str(source.get("grade") or "")
            if grade and grade not in GRADES:
                errors.append(f"{path.name}: sources[{index}] invalid grade {grade}")

    if "issue_map" not in payload:
        warnings.append(f"{path.name}: missing issue_map migration field")
    return errors, warnings


def validate_review_meta(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    payload = read_json(path)
    if not isinstance(payload, dict):
        return [f"{path.name}: invalid or missing JSON object"], warnings

    approval = str(payload.get("approval") or "")
    if approval not in REVIEW_APPROVALS:
        errors.append(f"{path.name}: invalid approval {approval!r}")

    comments = payload.get("comments")
    if comments is None:
        errors.append(f"{path.name}: missing comments")
    elif not isinstance(comments, list):
        errors.append(f"{path.name}: comments must be an array")
    else:
        for index, comment in enumerate(comments, start=1):
            if not isinstance(comment, dict):
                errors.append(f"{path.name}: comments[{index}] must be an object")
                continue
            for key in ("severity", "location", "issue", "recommendation"):
                if not str(comment.get(key) or "").strip():
                    errors.append(f"{path.name}: comments[{index}] missing {key}")
            severity = str(comment.get("severity") or "")
            if severity and severity not in REVIEW_SEVERITIES:
                errors.append(f"{path.name}: comments[{index}] invalid severity {severity}")
    return errors, warnings


def validate_case(case_dir: Path) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    event_errors, event_warnings = validate_events(case_dir)
    errors.extend(event_errors)
    warnings.extend(event_warnings)

    for meta_path in sorted(case_dir.glob("*-meta.json")):
        if meta_path.name == "review-meta.json":
            meta_errors, meta_warnings = validate_review_meta(meta_path)
        else:
            meta_errors, meta_warnings = validate_agent_meta(meta_path)
        errors.extend(meta_errors)
        warnings.extend(meta_warnings)

    if not any(case_dir.glob("*-meta.json")):
        warnings.append("no *-meta.json files found")
    return {"errors": errors, "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an orchestrator case directory.")
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("--mode", choices=("warn", "strict"), default="warn")
    args = parser.parse_args(argv)

    report = validate_case(args.case_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    for item in report["errors"]:
        print(f"[error] {item}", file=sys.stderr)
    for item in report["warnings"]:
        print(f"[warn] {item}", file=sys.stderr)
    return 1 if args.mode == "strict" and report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
