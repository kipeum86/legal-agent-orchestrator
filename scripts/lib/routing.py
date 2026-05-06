from __future__ import annotations

import os
from typing import Any

JURISDICTIONS = {"KR", "EU", "US", "US-CA", "California", "JP", "international", "multi", "other"}
DOMAINS = {"general", "data_protection", "game_regulation", "contract", "translation"}
TASKS = {"research", "drafting", "contract_review", "translation", "debate", "briefing"}
COMPLEXITIES = {"simple", "compound", "multi_domain", "adversarial"}
DATA_PROTECTION_AGENT = "data-protection-agent"
MERGED_DATA_PROTECTION_JURISDICTIONS = {"KR", "EU", "US", "US-CA", "California"}


def _split_token(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_split_token(item))
        return result
    text = str(value).strip()
    if not text or text == "—":
        return []
    parts = [part.strip() for part in text.replace("|", "+").split("+")]
    return [part for part in parts if part]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def normalize_classification(raw: dict[str, Any]) -> dict[str, Any]:
    jurisdictions = _dedupe(_split_token(raw.get("jurisdictions", raw.get("jurisdiction"))))
    domains = _dedupe(_split_token(raw.get("domains", raw.get("domain")))) or ["general"]
    tasks = _dedupe(_split_token(raw.get("tasks", raw.get("task")))) or ["research"]

    if "multi" in jurisdictions and len(jurisdictions) > 1:
        jurisdictions = [value for value in jurisdictions if value != "multi"]
    if not jurisdictions:
        jurisdictions = ["KR"] if "PIPA" in str(raw) else []

    complexity = str(raw.get("complexity") or "").strip()
    if complexity not in COMPLEXITIES:
        if "debate" in tasks:
            complexity = "adversarial"
        elif len(domains) > 1 or (len(jurisdictions) > 1 and "data_protection" in domains):
            complexity = "multi_domain"
        elif len(tasks) > 1:
            complexity = "compound"
        else:
            complexity = "simple"

    try:
        confidence = float(raw.get("confidence", 1.0))
    except (TypeError, ValueError):
        confidence = 0.0

    ambiguity = _split_token(raw.get("ambiguity"))
    return {
        "jurisdictions": jurisdictions,
        "domains": domains,
        "tasks": tasks,
        "complexity": complexity,
        "confidence": max(0.0, min(confidence, 1.0)),
        "ambiguity": ambiguity,
    }


def _unique_agents(agents: list[str]) -> list[str]:
    return _dedupe([agent for agent in agents if agent])


def _agent_profile() -> str:
    value = os.environ.get("LEGAL_ORCHESTRATOR_AGENT_PROFILE", "merged").strip().lower()
    return value if value in {"merged", "legacy"} else "merged"


def _legacy_data_protection_agents(jurisdictions: list[str]) -> list[str]:
    agents: list[str] = []
    if "KR" in jurisdictions:
        agents.append("PIPA-expert")
    if "EU" in jurisdictions:
        agents.append("GDPR-expert")
    if not jurisdictions or any(value not in {"KR", "EU"} for value in jurisdictions):
        agents.append("general-legal-research")
    return _unique_agents(agents)


def _data_protection_agents(jurisdictions: list[str]) -> list[str]:
    if _agent_profile() == "legacy":
        return _legacy_data_protection_agents(jurisdictions)

    if not jurisdictions:
        return [DATA_PROTECTION_AGENT]

    supported = [
        value for value in jurisdictions
        if value in MERGED_DATA_PROTECTION_JURISDICTIONS
    ]
    unsupported = [
        value for value in jurisdictions
        if value not in MERGED_DATA_PROTECTION_JURISDICTIONS and value not in {"multi"}
    ]
    agents = [DATA_PROTECTION_AGENT] if supported else []
    if unsupported:
        agents.append("general-legal-research")
    return _unique_agents(agents or ["general-legal-research"])


def _data_route_mode(base: str) -> str:
    return f"{base}_merged" if _agent_profile() == "merged" else base


def _with_writing_review(agents: list[str]) -> list[str]:
    return _unique_agents([*agents, "legal-writing-agent", "second-review-agent"])


def _sequential(pipeline: list[str], *, route_mode: str, notes: list[str] | None = None) -> dict[str, Any]:
    return {
        "pattern": "pattern_2",
        "execution": "sequential" if len(pipeline) > 1 else "single",
        "pipeline": pipeline,
        "route_mode": route_mode,
        "notes": notes or [],
    }


def _parallel(agents: list[str], *, route_mode: str, notes: list[str] | None = None) -> dict[str, Any]:
    parallel_agents = _unique_agents(agents)[:3]
    return {
        "pattern": "pattern_1",
        "execution": "parallel",
        "parallel_agents": parallel_agents,
        "pipeline": _with_writing_review(parallel_agents),
        "route_mode": route_mode,
        "notes": notes or [],
    }


def _debate_participants(domains: list[str], jurisdictions: list[str]) -> list[str]:
    if "data_protection" in domains:
        agents = _legacy_data_protection_agents(jurisdictions)
        if len(agents) >= 2:
            return agents[:2]
    if {"game_regulation", "data_protection"}.issubset(set(domains)):
        if "EU" in jurisdictions:
            return ["game-legal-research", "GDPR-expert"]
        if "KR" in jurisdictions:
            return ["game-legal-research", "PIPA-expert"]
    if "game_regulation" in domains:
        return ["game-legal-research", "general-legal-research"]
    return ["general-legal-research", "second-review-agent"]


def select_route(raw: dict[str, Any]) -> dict[str, Any]:
    classification = normalize_classification(raw)
    jurisdictions = classification["jurisdictions"]
    domains = classification["domains"]
    tasks = classification["tasks"]
    complexity = classification["complexity"]
    domain_set = set(domains)
    task_set = set(tasks)
    notes: list[str] = []

    if "briefing" in task_set:
        return {
            "classification": classification,
            "pattern": "out_of_scope",
            "execution": "external_tool",
            "pipeline": [],
            "route_mode": "briefing_not_orchestrated",
            "notes": ["briefing tools are operated outside the agent orchestrator"],
        }

    if complexity == "adversarial" or "debate" in task_set:
        participants = _debate_participants(domains, jurisdictions)
        return {
            "classification": classification,
            "pattern": "pattern_3",
            "execution": "debate",
            "pipeline": ["manage-debate"],
            "debate_participants": participants,
            "route_mode": "adversarial_debate",
            "notes": notes,
        }

    if "translation" in task_set and "contract" in domain_set:
        route = _sequential(
            ["contract-review-agent", "legal-translation-agent", "second-review-agent"],
            route_mode="contract_review_then_translation",
        )
        route["classification"] = classification
        return route

    if "translation" in task_set and domain_set.issubset({"translation", "general"}):
        route = _sequential(["legal-translation-agent"], route_mode="translation_only")
        route["classification"] = classification
        return route

    if "contract" in domain_set and "drafting" in task_set:
        route = _sequential(
            ["contract-review-agent", "second-review-agent"],
            route_mode="contract_drafting_wf5",
            notes=["contract drafting must use contract-review-agent WF5 drafting mode"],
        )
        route["classification"] = classification
        return route

    if {"contract", "data_protection"}.issubset(domain_set):
        agents = ["contract-review-agent", *_data_protection_agents(jurisdictions)]
        route = _parallel(agents, route_mode=_data_route_mode("contract_and_data_protection"))
        route["classification"] = classification
        return route

    if "contract_review" in task_set or ("contract" in domain_set and len(domain_set) == 1):
        route = _sequential(
            ["contract-review-agent", "second-review-agent"],
            route_mode="contract_review",
        )
        route["classification"] = classification
        return route

    if len(jurisdictions) >= 4:
        return {
            "classification": classification,
            "pattern": "needs_scope",
            "execution": "user_prompt",
            "pipeline": [],
            "route_mode": "multi_domain_truncated",
            "notes": ["more than three jurisdictions require scope reduction"],
        }

    if {"game_regulation", "data_protection"}.issubset(domain_set):
        agents = ["game-legal-research", *_data_protection_agents(jurisdictions)]
        route = _parallel(agents, route_mode=_data_route_mode("game_and_data_protection"))
        route["classification"] = classification
        return route

    if "data_protection" in domain_set and (complexity == "multi_domain" or len(jurisdictions) > 1):
        if _agent_profile() == "merged":
            agents = _data_protection_agents(jurisdictions)
            if len(agents) > 1:
                route = _parallel(agents, route_mode="multi_jurisdiction_data_merged")
            else:
                route = _sequential(
                    _with_writing_review(agents),
                    route_mode="multi_jurisdiction_data_merged",
                )
        else:
            route = _parallel(_data_protection_agents(jurisdictions), route_mode="multi_jurisdiction_data")
        route["classification"] = classification
        return route

    if "game_regulation" in domain_set:
        route = _sequential(
            ["game-legal-research", "legal-writing-agent", "second-review-agent"],
            route_mode="game_regulation",
        )
        route["classification"] = classification
        return route

    if "data_protection" in domain_set:
        route = _sequential(
            _with_writing_review(_data_protection_agents(jurisdictions)[:1]),
            route_mode=_data_route_mode("single_jurisdiction_data"),
        )
        route["classification"] = classification
        return route

    route = _sequential(
        ["general-legal-research", "legal-writing-agent", "second-review-agent"],
        route_mode="general_fallback",
    )
    route["classification"] = classification
    return route
