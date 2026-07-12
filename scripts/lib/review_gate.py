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

from scripts.lib.io_utils import read_json

APPROVED_STATUSES = {"approved", "approved_with_revisions"}
BLOCKING_STATUSES = {"revision_needed"}
VALID_STATUSES = APPROVED_STATUSES | BLOCKING_STATUSES


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


def evaluate_gate(case_dir: Path) -> GateResult:
    review_meta, review_path = load_review_meta(case_dir)
    if not isinstance(review_meta, dict):
        return GateResult(False, 2, "missing_review_meta", "missing", None, review_path)

    approval = normalize_approval(review_meta.get("approval"))
    if approval not in VALID_STATUSES:
        return GateResult(False, 2, "invalid_review_approval", approval or "missing", review_meta, review_path)

    if approval in BLOCKING_STATUSES:
        return GateResult(False, 3, "review_revision_needed", approval, review_meta, review_path)

    return GateResult(True, 0, None, approval, review_meta, review_path)
