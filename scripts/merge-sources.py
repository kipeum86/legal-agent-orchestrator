#!/usr/bin/env python3
"""Build deterministic sources.json from agent meta files and source events."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib.agents import AGENT_NAMES, agent_id_from_meta_filename  # noqa: E402
from scripts.lib.io_utils import parse_jsonl  # noqa: E402
from scripts.lib.review_gate import CITATION_STATUSES, load_review_meta  # noqa: E402

GRADES = ("A", "B", "C", "D")
VERIFICATION_STATUS_PRIORITY = {
    "verified": 0,
    "not_checked": 1,
    "unverified": 2,
    "nonexistent": 3,
}


def read_existing_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except OSError as exc:
        return None, f"{path.name}: {exc}"
    except json.JSONDecodeError as exc:
        return None, f"{path.name}: invalid JSON: {exc}"


def normalize_grade(value: Any) -> str:
    grade = str(value or "").strip().upper()
    return grade if grade in GRADES else "D"


def normalize_key(title: str, citation: str) -> tuple[str, str]:
    return (" ".join(title.split()).casefold(), " ".join(citation.split()).casefold())


def worst_verification_status(*statuses: str | None) -> str | None:
    valid = [status for status in statuses if status in VERIFICATION_STATUS_PRIORITY]
    if not valid:
        return None
    return max(valid, key=VERIFICATION_STATUS_PRIORITY.__getitem__)


def remember_worst(mapping: dict[Any, str], key: Any, status: str) -> None:
    mapping[key] = worst_verification_status(mapping.get(key), status) or status


def merge_sources(case_dir: Path) -> dict[str, Any]:
    per_agent: dict[str, dict[tuple[str, str], dict[str, Any]]] = defaultdict(dict)
    skipped_meta_files: list[str] = []

    def add_source(agent_id: str, source: dict[str, Any]) -> None:
        title = str(source.get("title") or source.get("source") or "제목 미기록").strip()
        citation = str(source.get("citation") or "").strip()
        grade = normalize_grade(source.get("grade"))
        entry = {
            "id": str(source.get("id") or "").strip() or None,
            "title": title,
            "grade": grade,
            "citation": citation,
        }
        for optional in ("pinpoint", "url_or_access", "relevance", "jurisdiction"):
            value = source.get(optional)
            if value:
                entry[optional] = value
        per_agent[agent_id][normalize_key(title, citation)] = {
            key: value for key, value in entry.items() if value is not None
        }

    for meta_path in sorted(case_dir.glob("*-meta.json")):
        payload, error = read_existing_json(meta_path)
        if error:
            skipped_meta_files.append(error)
            continue
        if not isinstance(payload, dict):
            skipped_meta_files.append(f"{meta_path.name}: expected JSON object")
            continue
        agent_id = agent_id_from_meta_filename(meta_path, strip_debate_round=True)
        sources = payload.get("sources")
        if isinstance(sources, list):
            for source in sources:
                if isinstance(source, dict):
                    add_source(agent_id, source)

    for event in parse_jsonl(case_dir / "events.jsonl"):
        if event.get("type") != "source_graded":
            continue
        data = event.get("data")
        if not isinstance(data, dict):
            continue
        agent_id = str(data.get("agent_id") or event.get("agent") or "unknown")
        add_source(agent_id, data)

    review_meta, _ = load_review_meta(case_dir)
    verification_by_agent_id: dict[tuple[str, str], str] = {}
    verification_by_agent_citation: dict[tuple[str, str], str] = {}
    legacy_verification_by_citation: dict[str, str] = {}
    raw_entries = review_meta.get("citation_verification") if isinstance(review_meta, dict) else None
    entries = [entry for entry in raw_entries if isinstance(entry, dict)] if isinstance(raw_entries, list) else []
    for entry in entries:
        status = str(entry.get("status") or "").strip().lower()
        if status not in CITATION_STATUSES:
            continue
        agent_id = str(entry.get("agent_id") or "").strip()
        source_id = str(entry.get("source_id") or "").strip()
        citation_key = " ".join(str(entry.get("citation") or "").split()).casefold()
        if agent_id:
            if source_id:
                remember_worst(verification_by_agent_id, (agent_id, source_id), status)
            elif citation_key:
                remember_worst(verification_by_agent_citation, (agent_id, citation_key), status)
        elif citation_key:
            remember_worst(legacy_verification_by_citation, citation_key, status)

    agents_payload = []
    grade_distribution = {grade: 0 for grade in GRADES}
    total_sources = 0
    for agent_id in sorted(per_agent):
        sources = sorted(
            per_agent[agent_id].values(),
            key=lambda source: (
                GRADES.index(source["grade"]) if source["grade"] in GRADES else len(GRADES),
                source["title"],
                source["citation"],
            ),
        )
        for source in sources:
            grade_distribution[source["grade"]] += 1
            source_id = str(source.get("id") or "").strip()
            citation_key = " ".join(str(source.get("citation") or "").split()).casefold()
            source["verification_status"] = worst_verification_status(
                verification_by_agent_id.get((agent_id, source_id)) if source_id else None,
                verification_by_agent_citation.get((agent_id, citation_key)) if citation_key else None,
                legacy_verification_by_citation.get(citation_key) if citation_key else None,
            ) or "not_checked"
        total_sources += len(sources)
        agents_payload.append(
            {
                "agent_id": agent_id,
                "agent_name": AGENT_NAMES.get(agent_id, agent_id),
                "sources": sources,
            }
        )

    if skipped_meta_files:
        raise ValueError("skipped meta files: " + "; ".join(skipped_meta_files))

    payload = {
        "case_id": case_dir.name,
        "total_sources": total_sources,
        "grade_distribution": grade_distribution,
        "verification_summary": {
            status: sum(
                1
                for agent in agents_payload
                for source in agent["sources"]
                if source.get("verification_status") == status
            )
            for status in sorted(CITATION_STATUSES)
        },
        "agents": agents_payload,
    }
    (case_dir / "sources.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Merge agent source metadata into sources.json.")
    parser.add_argument("case_dir", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = merge_sources(args.case_dir)
    except ValueError as exc:
        print(f"merge-sources: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
