#!/usr/bin/env python3
"""Build debate-transcript.md deterministically from debate round result files."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.sanitize import sanitize  # noqa: E402

RESULT_RE = re.compile(r"^debate-round-(\d+)-(.+)-result\.md$")

ROUND_LABELS = {
    1: "개시 의견",
    2: "반론",
    3: "최종 반론",
}

POSITION_LABELS = {
    "opinion": "의견",
    "rebuttal": "반론",
    "surrebuttal": "최종 반론",
}


@dataclass(frozen=True)
class DebateRoundArtifact:
    round_no: int
    agent_id: str
    result_path: Path
    meta_path: Path
    position: str


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


def debate_info(case_dir: Path) -> dict[str, Any]:
    info: dict[str, Any] = {
        "topic": "미기록",
        "framing": "",
        "participants": [],
        "rounds": None,
    }
    for event in parse_jsonl(case_dir / "events.jsonl"):
        if event.get("type") != "debate_initiated":
            continue
        data = event.get("data")
        if not isinstance(data, dict):
            continue
        info["topic"] = str(data.get("topic") or info["topic"])
        info["framing"] = str(data.get("framing") or info["framing"])
        participants = data.get("participants")
        if isinstance(participants, list):
            info["participants"] = [str(item) for item in participants]
    return info


def discover_artifacts(case_dir: Path, warnings: list[str]) -> list[DebateRoundArtifact]:
    artifacts: list[DebateRoundArtifact] = []
    for result_path in sorted(case_dir.glob("debate-round-*-*-result.md")):
        match = RESULT_RE.match(result_path.name)
        if match is None:
            continue
        round_no = int(match.group(1))
        agent_id = match.group(2)
        meta_path = case_dir / f"debate-round-{round_no}-{agent_id}-meta.json"
        meta = read_json(meta_path)
        if meta_path.exists() and not isinstance(meta, dict):
            warnings.append(f"{meta_path.name}: invalid JSON object; position fallback used")
        if not meta_path.exists():
            warnings.append(f"{meta_path.name}: missing; position fallback used")
        position = ""
        if isinstance(meta, dict):
            position = str(meta.get("position") or "")
        artifacts.append(
            DebateRoundArtifact(
                round_no=round_no,
                agent_id=agent_id,
                result_path=result_path,
                meta_path=meta_path,
                position=position,
            )
        )
    return artifacts


def _sanitise_header_value(value: Any, *, source: str, audit_entries: list[dict[str, Any]]) -> str:
    text = str(value or "")
    sanitised, matches = sanitize(text, source=source)
    if matches:
        audit_entries.append(
            {
                "source": source,
                "matches_count": len(matches),
                "unescaped_count": sum(1 for match in matches if not bool(match.get("escaped"))),
            }
        )
    return sanitised


def build_debate_transcript(
    case_dir: Path,
    *,
    output_path: Path | None = None,
    audit_path: Path | None = None,
) -> dict[str, Any]:
    case_dir = case_dir.resolve()
    output_path = output_path or case_dir / "debate-transcript.md"
    audit_path = audit_path or case_dir / "debate-transcript-audit.json"
    warnings: list[str] = []
    header_audit: list[dict[str, Any]] = []

    info = debate_info(case_dir)
    artifacts = discover_artifacts(case_dir, warnings)
    if not artifacts:
        raise ValueError(f"no debate round result files found in {case_dir}")

    participants = [str(agent) for agent in info.get("participants", [])]
    participant_order = {agent_id: index for index, agent_id in enumerate(participants)}
    artifacts.sort(
        key=lambda artifact: (
            artifact.round_no,
            participant_order.get(artifact.agent_id, len(participant_order)),
            artifact.agent_id,
        )
    )

    max_round = max(artifact.round_no for artifact in artifacts)
    topic = _sanitise_header_value(info.get("topic"), source="debate_initiated.topic", audit_entries=header_audit)
    framing = _sanitise_header_value(
        info.get("framing"), source="debate_initiated.framing", audit_entries=header_audit
    )
    participant_text = " vs ".join(participants) if participants else " / ".join(sorted({item.agent_id for item in artifacts}))
    participant_text = _sanitise_header_value(
        participant_text,
        source="debate_initiated.participants",
        audit_entries=header_audit,
    )

    lines = [
        "**MEMORANDUM**",
        "",
        "| | |",
        "|---|---|",
        "| **수 신** | 귀사 |",
        "| **참 조** | 법무·컴플라이언스 담당 |",
        "| **발 신** | Legal Agent Orchestrator |",
        f"| **제 목** | {topic} — 토론 트랜스크립트 |",
        "",
        "---",
        "",
        "## 토론 정보",
        "| | |",
        "|---|---|",
        f"| **Case ID** | {case_dir.name} |",
        f"| **주 제** | {topic} |",
        f"| **프레이밍** | {framing or '미기록'} |",
        f"| **참여자** | {participant_text} |",
        f"| **라운드** | {max_round} |",
        "",
    ]

    current_round: int | None = None
    round_audit: list[dict[str, Any]] = []
    for artifact in artifacts:
        if artifact.round_no != current_round:
            current_round = artifact.round_no
            label = ROUND_LABELS.get(artifact.round_no, f"Round {artifact.round_no}")
            lines.extend([f"## Round {artifact.round_no}: {label}", ""])

        raw_text = artifact.result_path.read_text(encoding="utf-8")
        sanitised_text, matches = sanitize(raw_text, source=artifact.result_path.name)
        position_label = POSITION_LABELS.get(artifact.position, artifact.position or "기록")
        lines.extend(
            [
                f"### {artifact.agent_id} — {position_label}",
                "",
                f"출처 파일: `{artifact.result_path.name}`",
                "",
                sanitised_text.rstrip(),
                "",
            ]
        )
        round_audit.append(
            {
                "round": artifact.round_no,
                "agent_id": artifact.agent_id,
                "position": artifact.position or None,
                "result_path": artifact.result_path.name,
                "meta_path": artifact.meta_path.name,
                "meta_exists": artifact.meta_path.exists(),
                "matches_count": len(matches),
                "unescaped_count": sum(1 for match in matches if not bool(match.get("escaped"))),
                "included_chars": len(raw_text),
            }
        )

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    payload = {
        "case_id": case_dir.name,
        "output": output_path.name,
        "audit": audit_path.name,
        "rounds_count": max_round,
        "artifacts_count": len(artifacts),
        "participants": participants,
        "warnings": warnings,
        "header_matches": header_audit,
        "rounds": round_audit,
    }
    audit_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministically build debate-transcript.md from debate result files."
    )
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--audit", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        payload = build_debate_transcript(args.case_dir, output_path=args.output, audit_path=args.audit)
    except (OSError, ValueError) as exc:
        print(f"build-debate-transcript: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
