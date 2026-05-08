#!/usr/bin/env python3
"""Build deterministic sources.json from agent meta files and source events."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

GRADES = ("A", "B", "C", "D")

AGENT_NAMES = {
    "legal-research-agent": "법률 리서치 스페셜리스트",
    "legal-writing-agent": "법률문서 작성 스페셜리스트",
    "second-review-agent": "시니어 리뷰 스페셜리스트",
    "data-protection-agent": "데이터보호 스페셜리스트",
}


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


def agent_from_meta_filename(path: Path) -> str:
    name = path.name
    if name == "writing-meta.json":
        return "legal-writing-agent"
    if name == "review-meta.json":
        return "second-review-agent"
    if name == "research-meta.json":
        return "legal-research-agent"
    if name.endswith("-meta.json"):
        return name[: -len("-meta.json")]
    return path.stem


def normalize_grade(value: Any) -> str:
    grade = str(value or "").strip().upper()
    return grade if grade in GRADES else "D"


def normalize_key(title: str, citation: str) -> tuple[str, str]:
    return (" ".join(title.split()).casefold(), " ".join(citation.split()).casefold())


def merge_sources(case_dir: Path) -> dict[str, Any]:
    per_agent: dict[str, dict[tuple[str, str], dict[str, Any]]] = defaultdict(dict)

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
        for optional in ("pinpoint", "url_or_access", "relevance"):
            value = source.get(optional)
            if value:
                entry[optional] = value
        per_agent[agent_id][normalize_key(title, citation)] = {
            key: value for key, value in entry.items() if value is not None
        }

    for meta_path in sorted(case_dir.glob("*-meta.json")):
        payload = read_json(meta_path)
        if not isinstance(payload, dict):
            continue
        agent_id = agent_from_meta_filename(meta_path)
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
        total_sources += len(sources)
        agents_payload.append(
            {
                "agent_id": agent_id,
                "agent_name": AGENT_NAMES.get(agent_id, agent_id),
                "sources": sources,
            }
        )

    payload = {
        "case_id": case_dir.name,
        "total_sources": total_sources,
        "grade_distribution": grade_distribution,
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
    payload = merge_sources(args.case_dir)
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
