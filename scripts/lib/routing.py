from __future__ import annotations

from typing import Any

JURISDICTIONS = {"KR", "EU", "US", "US-CA", "California", "JP", "international", "multi", "other"}
DOMAINS = {"general", "data_protection", "game_regulation", "contract", "translation"}
TASKS = {"research", "drafting", "contract_review", "translation", "debate", "briefing"}
COMPLEXITIES = {"simple", "compound", "multi_domain", "adversarial"}
DATA_PROTECTION_AGENT = "data-protection-agent"
LEGAL_RESEARCH_AGENT = "legal-research-agent"
DATA_PROTECTION_JURISDICTIONS = {"KR", "EU", "US", "US-CA"}
JURISDICTION_ALIASES = {"California": "US-CA"}
RETIRED_AGENT_IDS = frozenset({
    "contract-review-agent",
    "general-legal-research",
    "game-legal-research",
    "GDPR-expert",
    "legal-translation-agent",
    "PIPA-expert",
})


def derive_research_mode(domains: list[str]) -> str:
    """Map a classification's `domains` to a legal-research-agent research mode.

    Canonical modes per legal-research-agent intake contract: general,
    game_regulation, game_plus_general, fallback.
    """
    domain_set = set(domains)
    if {"game_regulation", "general"}.issubset(domain_set):
        return "game_plus_general"
    if "game_regulation" in domain_set:
        return "game_regulation"
    if domain_set.issubset({"general"}) or "general" in domain_set:
        return "general"
    return "fallback"


def normalize_jurisdiction(value: Any) -> str:
    """Return the canonical jurisdiction token without collapsing legal scope."""
    token = str(value or "").strip()
    return JURISDICTION_ALIASES.get(token, token)


def jurisdictions_compatible(declared: Any, source: Any) -> bool:
    """Whether a cited source jurisdiction fits a declared case jurisdiction."""
    declared_token = normalize_jurisdiction(declared)
    source_token = normalize_jurisdiction(source)
    if declared_token == source_token:
        return True
    return {declared_token, source_token} == {"US", "US-CA"}


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
    separators_normalized = text.replace("|", "+").replace(",", "+").replace("/", "+")
    parts = [part.strip() for part in separators_normalized.split("+")]
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
    jurisdictions = _dedupe([
        normalize_jurisdiction(value)
        for value in _split_token(raw.get("jurisdictions", raw.get("jurisdiction")))
    ])
    domains = _dedupe(_split_token(raw.get("domains", raw.get("domain")))) or ["general"]
    tasks = _dedupe(_split_token(raw.get("tasks", raw.get("task")))) or ["research"]

    if "multi" in jurisdictions and len(jurisdictions) > 1:
        jurisdictions = [value for value in jurisdictions if value != "multi"]

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


def _data_protection_agents(jurisdictions: list[str]) -> list[str]:
    if not jurisdictions:
        return [DATA_PROTECTION_AGENT]

    supported = [value for value in jurisdictions if value in DATA_PROTECTION_JURISDICTIONS]
    unsupported = [
        value for value in jurisdictions
        if value not in DATA_PROTECTION_JURISDICTIONS and value != "multi"
    ]
    agents = [DATA_PROTECTION_AGENT] if supported else []
    if unsupported:
        agents.append(LEGAL_RESEARCH_AGENT)
    return _unique_agents(agents or [LEGAL_RESEARCH_AGENT])


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
    if {"game_regulation", "data_protection"}.issubset(set(domains)):
        return [LEGAL_RESEARCH_AGENT, DATA_PROTECTION_AGENT]
    if "data_protection" in domains:
        return [DATA_PROTECTION_AGENT, LEGAL_RESEARCH_AGENT]
    return [LEGAL_RESEARCH_AGENT]


def _annotate_research_mode(route: dict[str, Any], domains: list[str]) -> dict[str, Any]:
    pipeline = route.get("pipeline") or []
    parallel = route.get("parallel_agents") or []
    if LEGAL_RESEARCH_AGENT in pipeline or LEGAL_RESEARCH_AGENT in parallel:
        route["agent_research_mode"] = derive_research_mode(domains)
    return route


def _assert_no_retired_agents(route: dict[str, Any]) -> dict[str, Any]:
    leaked: set[str] = set()
    for key in ("pipeline", "parallel_agents", "debate_participants"):
        values = route.get(key) or []
        if isinstance(values, list):
            leaked.update(str(value) for value in values if str(value) in RETIRED_AGENT_IDS)
    notes = route.get("notes") or []
    if isinstance(notes, list):
        note_text = "\n".join(str(note) for note in notes)
        leaked.update(agent_id for agent_id in RETIRED_AGENT_IDS if agent_id in note_text)
    if leaked:
        raise ValueError(f"Retired agent/repo IDs are forbidden in routes: {', '.join(sorted(leaked))}")
    return route


def _finalize_route(route: dict[str, Any], classification: dict[str, Any]) -> dict[str, Any]:
    route["classification"] = classification
    return _assert_no_retired_agents(_annotate_research_mode(route, classification["domains"]))


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
        return _finalize_route({
            "pattern": "out_of_scope",
            "execution": "external_tool",
            "pipeline": [],
            "route_mode": "briefing_not_orchestrated",
            "notes": ["briefing tools are operated outside the agent orchestrator"],
        }, classification)

    if complexity == "adversarial" or "debate" in task_set:
        participants = _debate_participants(domains, jurisdictions)
        route: dict[str, Any] = {
            "classification": classification,
            "pattern": "pattern_3" if len(participants) == 2 else "needs_scope",
            "execution": "debate" if len(participants) == 2 else "user_prompt",
            "pipeline": ["manage-debate"] if len(participants) == 2 else [],
            "debate_participants": participants,
            "route_mode": "adversarial_debate" if len(participants) == 2 else "debate_scope_required",
            "notes": notes
            if len(participants) == 2
            else [
                "debate requires two non-review participants; ask the user to define two opposing positions",
            ],
        }
        return _finalize_route(route, classification)

    if (
        "contract" in domain_set
        or "translation" in domain_set
        or "contract_review" in task_set
        or "translation" in task_set
    ):
        return _finalize_route({
            "pattern": "out_of_scope",
            "execution": "external_agent",
            "pipeline": [],
            "route_mode": "contract_or_translation_not_orchestrated",
            "notes": [
                "contract review and translation are outside this orchestrator; no agent dispatch is produced",
            ],
        }, classification)

    if len(jurisdictions) >= 4:
        return _finalize_route({
            "pattern": "needs_scope",
            "execution": "user_prompt",
            "pipeline": [],
            "route_mode": "multi_domain_truncated",
            "notes": ["more than three jurisdictions require scope reduction"],
        }, classification)

    if {"game_regulation", "data_protection"}.issubset(domain_set):
        agents = [LEGAL_RESEARCH_AGENT, *_data_protection_agents(jurisdictions)]
        route = _parallel(agents, route_mode="game_and_data_protection")
        return _finalize_route(route, classification)

    if "data_protection" in domain_set and (complexity == "multi_domain" or len(jurisdictions) > 1):
        agents = _data_protection_agents(jurisdictions)
        if len(agents) > 1:
            route = _parallel(agents, route_mode="multi_jurisdiction_data")
        else:
            route = _sequential(
                _with_writing_review(agents),
                route_mode="multi_jurisdiction_data",
            )
        return _finalize_route(route, classification)

    if "game_regulation" in domain_set:
        route = _sequential(
            [LEGAL_RESEARCH_AGENT, "legal-writing-agent", "second-review-agent"],
            route_mode="game_regulation",
        )
        return _finalize_route(route, classification)

    if "data_protection" in domain_set:
        route = _sequential(
            _with_writing_review(_data_protection_agents(jurisdictions)[:1]),
            route_mode="single_jurisdiction_data",
        )
        return _finalize_route(route, classification)

    route = _sequential(
        [LEGAL_RESEARCH_AGENT, "legal-writing-agent", "second-review-agent"],
        route_mode="general_fallback",
    )
    return _finalize_route(route, classification)
