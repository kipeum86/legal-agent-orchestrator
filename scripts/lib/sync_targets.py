from __future__ import annotations

from typing import Any

from scripts.lib.routing import RETIRED_AGENT_IDS

ACTIVE_AGENT_IDS = frozenset(
    {
        "legal-research-agent",
        "legal-writing-agent",
        "second-review-agent",
        "data-protection-agent",
    }
)
CONTROL_PLANE_ENTRIES = frozenset({"manage-debate"})
NO_DISPATCH_PATTERNS = frozenset({"out_of_scope", "needs_scope"})
NO_DISPATCH_EXECUTIONS = frozenset({"external_agent", "external_tool", "user_prompt"})


def _extend_route_values(route: dict[str, Any], key: str, values: list[str]) -> None:
    raw = route.get(key)
    if raw is None:
        return
    if not isinstance(raw, list):
        raise ValueError(f"{key} must be a JSON array")
    values.extend(str(value) for value in raw if str(value).strip())


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _is_no_dispatch_route(route: dict[str, Any]) -> bool:
    pattern = str(route.get("pattern") or "")
    execution = str(route.get("execution") or "")
    return pattern in NO_DISPATCH_PATTERNS or execution in NO_DISPATCH_EXECUTIONS


def resolve_sync_targets(route: dict[str, Any]) -> list[str]:
    """Return active subordinate agents that must be synced before dispatch."""

    candidates: list[str] = []
    for key in ("pipeline", "parallel_agents", "debate_participants"):
        _extend_route_values(route, key, candidates)

    candidates = [value for value in candidates if value not in CONTROL_PLANE_ENTRIES]
    leaked_retired = sorted(value for value in candidates if value in RETIRED_AGENT_IDS)
    if leaked_retired:
        raise ValueError(f"retired agent/repo IDs cannot be sync targets: {', '.join(leaked_retired)}")

    unknown = sorted(value for value in candidates if value not in ACTIVE_AGENT_IDS)
    if unknown:
        raise ValueError(f"unknown sync target agent IDs: {', '.join(unknown)}")

    if _is_no_dispatch_route(route):
        return []

    targets = _dedupe(candidates)
    if str(route.get("execution") or "") == "debate":
        targets = _dedupe([*targets, "legal-writing-agent", "second-review-agent"])
    return targets
