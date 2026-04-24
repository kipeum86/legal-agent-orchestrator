#!/usr/bin/env python3
"""Decide whether Pattern 3 should run debate Round 3 from round meta files."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROUND_META_RE = re.compile(r"^debate-round-(\d+)-(.+)-meta\.json$")


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


def participants_from_events(case_dir: Path) -> list[str]:
    for event in parse_jsonl(case_dir / "events.jsonl"):
        if event.get("type") != "debate_initiated":
            continue
        data = event.get("data")
        if not isinstance(data, dict):
            continue
        participants = data.get("participants")
        if isinstance(participants, list):
            return [str(item) for item in participants if str(item).strip()]
    return []


def participants_from_meta(case_dir: Path) -> list[str]:
    agents: set[str] = set()
    for path in case_dir.glob("debate-round-*-*-meta.json"):
        match = ROUND_META_RE.match(path.name)
        if match is None:
            continue
        round_no = int(match.group(1))
        if round_no in {1, 2}:
            agents.add(match.group(2))
    return sorted(agents)


def load_meta(case_dir: Path, round_no: int, agent_id: str) -> dict[str, Any] | None:
    payload = read_json(case_dir / f"debate-round-{round_no}-{agent_id}-meta.json")
    return payload if isinstance(payload, dict) else None


def string_list(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    return [str(item).strip() for item in value if str(item).strip()]


def normalise_claim(value: str) -> str:
    return " ".join(value.split()).casefold()


def insufficient_payload(case_dir: Path, participants: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "proceed": True,
        "reason": "insufficient_meta",
        "conceded_ratio": None,
        "contested_claims": [],
        "participants": participants,
        "ratios": [],
        "warnings": warnings,
        "case_id": case_dir.name,
    }


def decide_round3(case_dir: Path) -> dict[str, Any]:
    case_dir = case_dir.resolve()
    warnings: list[str] = []
    participants = participants_from_events(case_dir)
    if len(participants) != 2:
        derived = participants_from_meta(case_dir)
        if len(derived) == 2:
            warnings.append("debate_initiated participants missing or not exactly 2; derived from meta files")
            participants = derived
        else:
            warnings.append("could not determine exactly 2 debate participants")
            return insufficient_payload(case_dir, participants, warnings)

    round1_claims: dict[str, list[str]] = {}
    round2_concessions: dict[str, list[str]] = {}
    round2_rebuts: dict[str, str] = {}

    for agent_id in participants:
        round1_meta = load_meta(case_dir, 1, agent_id)
        if round1_meta is None:
            warnings.append(f"debate-round-1-{agent_id}-meta.json missing or invalid")
            return insufficient_payload(case_dir, participants, warnings)
        claims = string_list(round1_meta.get("key_claims"))
        if claims is None:
            warnings.append(f"debate-round-1-{agent_id}-meta.json key_claims must be an array")
            return insufficient_payload(case_dir, participants, warnings)
        round1_claims[agent_id] = claims

        round2_meta = load_meta(case_dir, 2, agent_id)
        if round2_meta is None:
            warnings.append(f"debate-round-2-{agent_id}-meta.json missing or invalid")
            return insufficient_payload(case_dir, participants, warnings)
        concessions = string_list(round2_meta.get("conceded_points"))
        if concessions is None:
            warnings.append(f"debate-round-2-{agent_id}-meta.json conceded_points must be an array")
            return insufficient_payload(case_dir, participants, warnings)
        round2_concessions[agent_id] = concessions

        default_rebuts = next(participant for participant in participants if participant != agent_id)
        rebuts_agent = str(round2_meta.get("rebuts_agent") or default_rebuts)
        if rebuts_agent not in participants or rebuts_agent == agent_id:
            warnings.append(
                f"debate-round-2-{agent_id}-meta.json rebuts_agent invalid; using counterpart"
            )
            rebuts_agent = default_rebuts
        round2_rebuts[agent_id] = rebuts_agent

    ratios: list[dict[str, Any]] = []
    contested_claims: list[str] = []
    for agent_id in participants:
        rebuts_agent = round2_rebuts[agent_id]
        claims = round1_claims[rebuts_agent]
        concessions = round2_concessions[agent_id]
        denominator = max(1, len(claims))
        ratio = min(1.0, len(concessions) / denominator)
        conceded_lookup = {normalise_claim(item) for item in concessions}
        contested_claims.extend(
            claim for claim in claims if normalise_claim(claim) not in conceded_lookup
        )
        ratios.append(
            {
                "agent_id": agent_id,
                "rebuts_agent": rebuts_agent,
                "conceded_points_count": len(concessions),
                "opponent_key_claims_count": len(claims),
                "ratio": round(ratio, 6),
            }
        )

    conceded_ratio = round(sum(item["ratio"] for item in ratios) / len(ratios), 6)
    proceed = conceded_ratio < 0.5
    return {
        "proceed": proceed,
        "reason": "significant_disagreement" if proceed else "convergence",
        "conceded_ratio": conceded_ratio,
        "contested_claims": contested_claims,
        "participants": participants,
        "ratios": ratios,
        "warnings": warnings,
        "case_id": case_dir.name,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Decide Pattern 3 debate Round 3 from Round 1/2 meta files."
    )
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("--out", type=Path, default=None, help="Optional JSON output file.")
    args = parser.parse_args(argv)

    payload = decide_round3(args.case_dir)
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if args.out is not None:
        args.out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
