from __future__ import annotations

import re
from pathlib import Path
from typing import Final

AGENT_PROFILES: Final[dict[str, dict[str, str]]] = {
    "legal-research-agent": {
        "name": "법률 리서치 스페셜리스트",
        "role": "범용 + 게임산업 법률 리서치",
    },
    "legal-writing-agent": {
        "name": "법률문서 작성 스페셜리스트",
        "role": "법률문서 작성",
    },
    "second-review-agent": {
        "name": "시니어 리뷰 스페셜리스트",
        "role": "품질 검토, 최종 승인",
    },
    "data-protection-agent": {
        "name": "데이터보호 스페셜리스트",
        "role": "KR PIPA, EU GDPR, California CCPA/CPRA",
    },
}

AGENT_NAMES: Final[dict[str, str]] = {
    agent_id: profile["name"] for agent_id, profile in AGENT_PROFILES.items()
}

DEBATE_ROUND_META_RE: Final[re.Pattern[str]] = re.compile(r"^debate-round-\d+-")


def is_debate_round_meta(path: Path) -> bool:
    return DEBATE_ROUND_META_RE.match(path.name) is not None


def agent_id_from_meta_filename(path: Path, *, strip_debate_round: bool = False) -> str:
    name = path.name
    if strip_debate_round:
        name = DEBATE_ROUND_META_RE.sub("", name)
    if name == "research-meta.json":
        return "legal-research-agent"
    if name == "writing-meta.json":
        return "legal-writing-agent"
    if name == "review-meta.json":
        return "second-review-agent"
    if name.endswith("-meta.json"):
        return name[: -len("-meta.json")]
    return path.stem
