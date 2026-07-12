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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib.io_utils import parse_jsonl_strict, read_json  # noqa: E402

GRADES = {"A", "B", "C", "D"}
REVIEW_APPROVALS = {"approved", "approved_with_revisions", "revision_needed"}
REVIEW_SEVERITIES = {"critical", "major", "minor", "suggestion"}
ROUTING_COMPLEXITIES = {"simple", "compound", "multi_domain", "adversarial"}
CITATION_STATUSES = {"verified", "nonexistent", "unverified", "not_checked"}


def require_mapping(value: Any, label: str, errors: list[str]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    errors.append(f"{label}: expected object")
    return {}


def validate_events(case_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    events, parse_errors = parse_jsonl_strict(case_dir / "events.jsonl")
    errors.extend(parse_errors)

    seen_ids: set[str] = set()
    final_event_count = 0
    for index, event in enumerate(events, start=1):
        label = f"events.jsonl:{index}"
        for key in ("id", "ts", "agent", "type", "data"):
            if key not in event:
                errors.append(f"{label}: missing {key}")
        event_id = str(event.get("id") or "")
        if not event_id:
            pass
        elif event_id == "evt_final":
            final_event_count += 1
            if final_event_count > 1:
                errors.append(f"{label}: duplicate event id evt_final")
        elif event_id in seen_ids:
            errors.append(f"{label}: duplicate event id {event_id}")
        elif event_id:
            seen_ids.add(event_id)

        data = require_mapping(event.get("data"), f"{label}.data", errors)
        event_type = str(event.get("type") or "")
        if event_type == "case_classified":
            for key in ("jurisdictions", "domains", "tasks", "complexity", "confidence", "pipeline", "pattern"):
                if key not in data:
                    errors.append(f"{label}: case_classified.data missing {key}")
            for key in ("jurisdictions", "domains", "tasks", "pipeline"):
                if key in data and not isinstance(data.get(key), list):
                    errors.append(f"{label}: case_classified.data.{key} must be an array")
            complexity = str(data.get("complexity") or "")
            if complexity and complexity not in ROUTING_COMPLEXITIES:
                errors.append(f"{label}: invalid complexity {complexity}")
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

    citation_entries = payload.get("citation_verification")
    if citation_entries is None:
        errors.append(f"{path.name}: missing citation_verification")
    elif not isinstance(citation_entries, list):
        errors.append(f"{path.name}: citation_verification must be an array")
    else:
        for index, entry in enumerate(citation_entries, start=1):
            if not isinstance(entry, dict):
                errors.append(f"{path.name}: citation_verification[{index}] must be an object")
                continue
            if not str(entry.get("citation") or "").strip():
                errors.append(f"{path.name}: citation_verification[{index}] missing citation")
            status = str(entry.get("status") or "").strip().lower()
            if status not in CITATION_STATUSES:
                errors.append(f"{path.name}: citation_verification[{index}] invalid status {status!r}")
    return errors, warnings


def is_review_meta_path(path: Path) -> bool:
    return (
        path.name == "review-meta.json"
        or path.name == "second-review-agent-meta.json"
        or (path.name.endswith("-meta.json") and "review" in path.stem)
    )


def validate_case(case_dir: Path) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    event_errors, event_warnings = validate_events(case_dir)
    errors.extend(event_errors)
    warnings.extend(event_warnings)

    for meta_path in sorted(case_dir.glob("*-meta.json")):
        if is_review_meta_path(meta_path):
            meta_errors, meta_warnings = validate_review_meta(meta_path)
        else:
            meta_errors, meta_warnings = validate_agent_meta(meta_path)
        errors.extend(meta_errors)
        warnings.extend(meta_warnings)

    classification = read_json(case_dir / "classification.json")
    if isinstance(classification, dict):
        declared = {str(j) for j in classification.get("jurisdictions") or [] if str(j).strip()}
        declared = {"US-CA" if j == "California" else j for j in declared}
        if declared and not declared & {"multi", "other"}:
            allowed = declared | {"international"}
            for meta_path in sorted(case_dir.glob("*-meta.json")):
                if is_review_meta_path(meta_path):
                    continue
                payload = read_json(meta_path)
                sources = payload.get("sources") if isinstance(payload, dict) else None
                if not isinstance(sources, list):
                    continue
                for index, source in enumerate(sources, start=1):
                    if not isinstance(source, dict):
                        continue
                    jurisdiction = str(source.get("jurisdiction") or "").strip()
                    jurisdiction = "US-CA" if jurisdiction == "California" else jurisdiction
                    if jurisdiction and jurisdiction not in allowed:
                        errors.append(
                            f"{meta_path.name}: sources[{index}] jurisdiction_mismatch: "
                            f"{jurisdiction} not in classification {sorted(allowed)}"
                        )

    if not any(case_dir.glob("*-meta.json")):
        warnings.append("no *-meta.json files found")
    return {"errors": errors, "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an orchestrator case directory.")
    parser.add_argument("case_dir", type=Path, nargs="?", default=None)
    parser.add_argument("--meta", type=Path, default=None,
                        help="Validate a single *-meta.json file (always strict).")
    parser.add_argument("--mode", choices=("warn", "strict"), default="warn")
    args = parser.parse_args(argv)

    if args.meta is not None:
        if is_review_meta_path(args.meta):
            errors, warnings = validate_review_meta(args.meta)
        else:
            errors, warnings = validate_agent_meta(args.meta)
        report = {"errors": errors, "warnings": warnings}
    elif args.case_dir is not None:
        report = validate_case(args.case_dir)
    else:
        parser.error("provide a case_dir or --meta")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    for item in report["errors"]:
        print(f"[error] {item}", file=sys.stderr)
    for item in report["warnings"]:
        print(f"[warn] {item}", file=sys.stderr)
    if args.meta is not None:
        return 1 if report["errors"] else 0
    return 1 if args.mode == "strict" and report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
