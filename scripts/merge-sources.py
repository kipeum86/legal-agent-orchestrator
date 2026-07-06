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

GRADES = ("A", "B", "C", "D")


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
        for optional in ("pinpoint", "url_or_access", "relevance"):
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

    if skipped_meta_files:
        raise ValueError("skipped meta files: " + "; ".join(skipped_meta_files))

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
    try:
        payload = merge_sources(args.case_dir)
    except ValueError as exc:
        print(f"merge-sources: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
