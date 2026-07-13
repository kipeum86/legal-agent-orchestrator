"""Deterministic release-gate evaluation for a case directory.

Single source of truth for INV-1. finalize-case.py (audit-record gate) and
md-to-docx.py (artifact gate) both call evaluate_gate() so the decision cannot
drift between the event log and the deliverable files.

Exit-code convention carried in GateResult.exit_code:
  0 = gate passes
  2 = structural problem (review meta missing/invalid) - never overridable
  3 = review gate blocked - overridable only via finalize-case --allow-unapproved
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.lib.io_utils import parse_jsonl, read_json

APPROVED_STATUSES = {"approved"}
PENDING_STATUSES = {"approved_with_revisions"}
BLOCKING_STATUSES = {"revision_needed"}
VALID_STATUSES = APPROVED_STATUSES | PENDING_STATUSES | BLOCKING_STATUSES
BINDING_FILENAME = "review-binding.json"
BINDABLE_DELIVERABLES = ("opinion.md", "debate-opinion.md", "debate-transcript.md")
CITATION_STATUSES = {"verified", "nonexistent", "unverified", "not_checked"}
FAILING_CITATION_STATUSES = {"nonexistent", "unverified"}


@dataclass
class GateResult:
    ok: bool
    exit_code: int
    reason: str | None
    approval: str
    review_meta: dict[str, Any] | None
    review_path: Path | None
    detail: dict[str, Any] = field(default_factory=dict)


def sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def normalize_approval(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def load_review_meta(case_dir: Path) -> tuple[dict[str, Any] | None, Path | None]:
    candidates = [case_dir / "review-meta.json", case_dir / "second-review-agent-meta.json"]
    candidates.extend(path for path in sorted(case_dir.glob("*review*-meta.json")) if path not in candidates)
    for path in candidates:
        payload = read_json(path)
        if isinstance(payload, dict):
            return payload, path
    return None, None


def _check_binding(case_dir: Path, review_path: Path | None) -> tuple[str | None, dict[str, Any]]:
    binding = read_json(case_dir / BINDING_FILENAME)
    if not isinstance(binding, dict):
        return "missing_review_binding", {}
    reviewed = binding.get("reviewed")
    if not isinstance(reviewed, dict) or not reviewed:
        return "missing_review_binding", {"note": "binding has no reviewed files"}
    if review_path is None or sha256_file(review_path) != binding.get("review_meta_sha256"):
        return "stale_review_binding", {"mismatch": "review-meta"}
    bound_files = {str(name) for name in reviewed}
    current_files = {
        name
        for name in BINDABLE_DELIVERABLES
        if (case_dir / name).is_file()
    }
    if bound_files != current_files:
        return "stale_review_binding", {
            "mismatch": "reviewed_files",
            "bound_files": sorted(bound_files),
            "current_files": sorted(current_files),
        }
    for name, digest in reviewed.items():
        if sha256_file(case_dir / str(name)) != digest:
            return "stale_review_binding", {"mismatch": str(name)}
    return None, {"binding_files": sorted(str(name) for name in reviewed)}


def _check_verbatim(case_dir: Path) -> tuple[str | None, dict[str, Any]]:
    for event in reversed(parse_jsonl(case_dir / "events.jsonl")):
        if event.get("type") not in {"verbatim_verified", "mcp_fallback_verification"}:
            continue
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        passed = data.get("passed")
        if passed is False:
            return "verbatim_verification_failed", {"verbatim_event_id": event.get("id")}
        if passed is True:
            return None, {"verbatim": "passed"}
        return None, {"verbatim": "legacy_event_without_passed"}
    return None, {"verbatim": "not_run"}


def _check_citations(review_meta: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    entries = review_meta.get("citation_verification")
    if not isinstance(entries, list):
        return "citation_verification_missing", {}
    counts: dict[str, int] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            return "citation_verification_missing", {"note": "entry is not an object"}
        status = str(entry.get("status") or "").strip().lower()
        if status not in CITATION_STATUSES:
            return "citation_verification_missing", {"note": f"invalid status {status!r}"}
        counts[status] = counts.get(status, 0) + 1
    failing = sum(counts.get(status, 0) for status in FAILING_CITATION_STATUSES)
    if failing:
        return "citation_verification_failed", {"citation_counts": counts}
    return None, {"citation_counts": counts}


def evaluate_gate(case_dir: Path) -> GateResult:
    review_meta, review_path = load_review_meta(case_dir)
    if not isinstance(review_meta, dict):
        return GateResult(False, 2, "missing_review_meta", "missing", None, review_path)

    approval = normalize_approval(review_meta.get("approval"))
    if approval not in VALID_STATUSES:
        return GateResult(False, 2, "invalid_review_approval", approval or "missing", review_meta, review_path)

    if approval in BLOCKING_STATUSES:
        return GateResult(False, 3, "review_revision_needed", approval, review_meta, review_path)

    if approval in PENDING_STATUSES:
        return GateResult(False, 3, "review_revisions_pending", approval, review_meta, review_path)

    detail: dict[str, Any] = {}
    reason, binding_detail = _check_binding(case_dir, review_path)
    detail.update(binding_detail)
    if reason:
        return GateResult(False, 3, reason, approval, review_meta, review_path, detail)

    reason, citation_detail = _check_citations(review_meta)
    detail.update(citation_detail)
    if reason:
        return GateResult(False, 3, reason, approval, review_meta, review_path, detail)

    reason, verbatim_detail = _check_verbatim(case_dir)
    detail.update(verbatim_detail)
    if reason:
        return GateResult(False, 3, reason, approval, review_meta, review_path, detail)

    return GateResult(True, 0, None, approval, review_meta, review_path, detail)
