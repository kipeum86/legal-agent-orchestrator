from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.lib.routing import RETIRED_AGENT_IDS
from scripts.lib.sync_targets import ACTIVE_AGENT_IDS

DEFAULT_TTL_SECONDS = 600
STATE_VERSION = 1
DEFAULT_BRANCH = "main"


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def read_targets(path: Path) -> list[str]:
    payload = read_json(path)
    if not isinstance(payload, list):
        raise ValueError("targets file must contain a JSON array")
    return [str(item) for item in payload if str(item).strip()]


def validate_targets(targets: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for target in targets:
        if target in RETIRED_AGENT_IDS:
            raise ValueError(f"retired agent/repo ID cannot be synced: {target}")
        if target not in ACTIVE_AGENT_IDS:
            raise ValueError(f"unknown sync target agent ID: {target}")
        if target not in seen:
            seen.add(target)
            result.append(target)
    return result


def load_state(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        return {"version": STATE_VERSION, "default_branch": DEFAULT_BRANCH, "agents": {}}
    agents = payload.get("agents")
    if not isinstance(agents, dict):
        payload["agents"] = {}
    payload.setdefault("version", STATE_VERSION)
    payload.setdefault("default_branch", DEFAULT_BRANCH)
    return payload


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_ttl(env: dict[str, str]) -> int:
    raw = env.get("LEGAL_ORCHESTRATOR_AGENT_SYNC_TTL_SECONDS")
    if raw is None or raw == "":
        return DEFAULT_TTL_SECONDS
    try:
        ttl = int(raw)
    except ValueError as exc:
        raise ValueError("LEGAL_ORCHESTRATOR_AGENT_SYNC_TTL_SECONDS must be an integer") from exc
    if ttl < 0:
        raise ValueError("LEGAL_ORCHESTRATOR_AGENT_SYNC_TTL_SECONDS must be >= 0")
    return ttl


def checkout_head(agent_dir: Path, repo_root: Path) -> str | None:
    if not (agent_dir / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "-C", str(agent_dir), "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def decide_sync_plan(
    targets: list[str],
    *,
    agents_dir: Path,
    state: dict[str, Any],
    env: dict[str, str],
    now: datetime,
) -> tuple[list[str], list[dict[str, str]], int, bool, bool]:
    targets = validate_targets(targets)
    ttl_seconds = parse_ttl(env)
    skip_all = env.get("LEGAL_ORCHESTRATOR_SKIP_AGENT_SYNC") == "1"
    force = env.get("LEGAL_ORCHESTRATOR_FORCE_AGENT_SYNC") == "1"
    skipped: list[dict[str, str]] = []
    to_sync: list[str] = []

    if skip_all:
        return [], [{"agent_id": target, "reason": "env_skip"} for target in targets], ttl_seconds, force, skip_all

    agents_state = state.get("agents")
    if not isinstance(agents_state, dict):
        agents_state = {}

    for target in targets:
        agent_dir = agents_dir / target
        if agent_dir.is_symlink():
            skipped.append({"agent_id": target, "reason": "symlink"})
            continue
        if not agent_dir.exists():
            to_sync.append(target)
            continue
        if not (agent_dir / ".git").exists():
            to_sync.append(target)
            continue
        if force:
            to_sync.append(target)
            continue
        if ttl_seconds == 0:
            to_sync.append(target)
            continue

        entry = agents_state.get(target)
        last_success = parse_timestamp(entry.get("last_success_at")) if isinstance(entry, dict) else None
        if last_success is None:
            to_sync.append(target)
            continue
        if last_success + timedelta(seconds=ttl_seconds) >= now:
            skipped.append({"agent_id": target, "reason": "ttl"})
        else:
            to_sync.append(target)

    return to_sync, skipped, ttl_seconds, force, skip_all


def update_attempt_state(
    state: dict[str, Any],
    *,
    targets: list[str],
    status: str,
    now: datetime,
    repo_root: Path,
    agents_dir: Path,
    success: bool,
) -> None:
    agents_state = state.setdefault("agents", {})
    if not isinstance(agents_state, dict):
        state["agents"] = agents_state = {}
    for target in targets:
        entry = agents_state.get(target)
        if not isinstance(entry, dict):
            entry = {}
        entry["last_attempt_at"] = format_timestamp(now)
        entry["status"] = status
        head = checkout_head(agents_dir / target, repo_root)
        if head:
            entry["head"] = head
        if success:
            entry["last_success_at"] = format_timestamp(now)
        agents_state[target] = entry


def sync_agents(
    targets: list[str],
    *,
    repo_root: Path,
    agents_dir: Path | None = None,
    state_path: Path | None = None,
    setup_script: Path | None = None,
    env: dict[str, str] | None = None,
    now: datetime | None = None,
    dry_run: bool = False,
) -> tuple[dict[str, Any], int]:
    if env is None:
        env = os.environ.copy()
    else:
        merged_env = os.environ.copy()
        merged_env.update(env)
        env = merged_env
    now = now or utc_now()
    agents_dir = agents_dir or repo_root / "agents"
    state_path = state_path or agents_dir / ".sync-state.json"
    setup_script = setup_script or repo_root / "setup.sh"
    targets = validate_targets(targets)

    state = load_state(state_path)
    to_sync, skipped, ttl_seconds, force, skip_all = decide_sync_plan(
        targets,
        agents_dir=agents_dir,
        state=state,
        env=env,
        now=now,
    )

    result: dict[str, Any] = {
        "method": "sync-agents",
        "targets": targets,
        "synced": [],
        "skipped": skipped,
        "failed": [],
        "ttl_seconds": ttl_seconds,
        "force": force,
        "skip": skip_all,
        "dry_run": dry_run,
        "state_path": str(state_path),
    }

    if not targets:
        result["status"] = "skipped"
        result["reason"] = "no_targets"
        return result, 0

    if not to_sync:
        result["status"] = "skipped"
        result["reason"] = "all_targets_skipped"
        return result, 0

    if dry_run:
        result["status"] = "dry_run"
        result["would_sync"] = to_sync
        return result, 0

    completed = subprocess.run(
        ["bash", str(setup_script), "update", *to_sync],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    result["setup_returncode"] = completed.returncode
    result["setup_stdout"] = completed.stdout
    result["setup_stderr"] = completed.stderr

    if completed.returncode == 0:
        update_attempt_state(
            state,
            targets=to_sync,
            status="ok",
            now=now,
            repo_root=repo_root,
            agents_dir=agents_dir,
            success=True,
        )
        write_state(state_path, state)
        result["status"] = "ok"
        result["synced"] = to_sync
        return result, 0

    update_attempt_state(
        state,
        targets=to_sync,
        status="failed",
        now=now,
        repo_root=repo_root,
        agents_dir=agents_dir,
        success=False,
    )
    write_state(state_path, state)
    recoverable = all((agents_dir / target).exists() for target in to_sync)
    result["status"] = "failed"
    result["failed"] = to_sync
    result["recoverable"] = recoverable
    if recoverable:
        result["fallback"] = "cached_versions"
        return result, 0
    return result, 1
