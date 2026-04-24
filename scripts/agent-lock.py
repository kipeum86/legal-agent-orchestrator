#!/usr/bin/env python3
"""Manage locked subordinate agent checkouts for the orchestrator."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


class AgentLockError(RuntimeError):
    pass


def run_git(args: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        command = "git " + " ".join(args)
        detail = result.stderr.strip() or result.stdout.strip()
        raise AgentLockError(f"{command} failed: {detail}")
    return result


def read_lock(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentLockError(f"cannot read lock file {path}: {exc}") from exc
    agents = payload.get("agents")
    if not isinstance(agents, dict) or not agents:
        raise AgentLockError(f"{path}: missing agents object")
    for agent_id, entry in agents.items():
        if not isinstance(entry, dict):
            raise AgentLockError(f"{path}: {agent_id} entry must be an object")
        for key in ("repo", "commit"):
            if not str(entry.get(key) or "").strip():
                raise AgentLockError(f"{path}: {agent_id} missing {key}")
    return payload


def write_lock(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_git_worktree(path: Path) -> bool:
    result = run_git(["-C", str(path), "rev-parse", "--is-inside-work-tree"], check=False)
    return result.returncode == 0 and result.stdout.strip() == "true"


def current_commit(path: Path) -> str | None:
    result = run_git(["-C", str(path), "rev-parse", "HEAD"], check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def current_branch(path: Path) -> str | None:
    result = run_git(["-C", str(path), "branch", "--show-current"], check=False)
    branch = result.stdout.strip()
    return branch or None


def dirty_state(path: Path) -> str:
    result = run_git(["-C", str(path), "status", "--porcelain"], check=False)
    if result.returncode != 0:
        return "unknown"
    return "dirty" if result.stdout.strip() else "clean"


def commit_exists(path: Path, commit: str) -> bool:
    result = run_git(["-C", str(path), "cat-file", "-e", f"{commit}^{{commit}}"], check=False)
    return result.returncode == 0


def ahead_behind(path: Path, locked_commit: str) -> dict[str, int | None]:
    if not commit_exists(path, locked_commit):
        return {"ahead": None, "behind": None}
    result = run_git(
        ["-C", str(path), "rev-list", "--left-right", "--count", f"{locked_commit}...HEAD"],
        check=False,
    )
    if result.returncode != 0:
        return {"ahead": None, "behind": None}
    left, right = result.stdout.strip().split()
    return {"ahead": int(right), "behind": int(left)}


def ensure_checkout(agents_dir: Path, agent_id: str, entry: dict[str, Any]) -> dict[str, Any]:
    target = agents_dir / agent_id
    repo = str(entry["repo"])
    locked_commit = str(entry["commit"])
    result: dict[str, Any] = {"agent_id": agent_id, "path": str(target), "locked_commit": locked_commit}

    if target.is_symlink():
        result.update(
            {
                "status": "symlink_skipped",
                "current_commit": current_commit(target),
                "dirty": dirty_state(target),
                "message": "development symlink left untouched",
            }
        )
        return result

    if target.exists() and not is_git_worktree(target):
        raise AgentLockError(f"{target} exists but is not a git worktree")

    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        run_git(["clone", repo, str(target)])
        result["cloned"] = True

    if dirty_state(target) == "dirty":
        raise AgentLockError(f"{agent_id}: worktree is dirty; refusing to checkout locked commit")

    if not commit_exists(target, locked_commit):
        run_git(["-C", str(target), "fetch", "--tags", "origin"])
    if not commit_exists(target, locked_commit):
        raise AgentLockError(f"{agent_id}: locked commit {locked_commit} is not available")

    run_git(["-C", str(target), "checkout", "--detach", locked_commit])
    result.update(
        {
            "status": "locked",
            "current_commit": current_commit(target),
            "dirty": dirty_state(target),
        }
    )
    return result


def sync_agents(lock_path: Path, agents_dir: Path) -> list[dict[str, Any]]:
    lock = read_lock(lock_path)
    return [
        ensure_checkout(agents_dir, agent_id, entry)
        for agent_id, entry in lock["agents"].items()
    ]


def status_agents(lock_path: Path, agents_dir: Path) -> list[dict[str, Any]]:
    lock = read_lock(lock_path)
    rows: list[dict[str, Any]] = []
    for agent_id, entry in lock["agents"].items():
        target = agents_dir / agent_id
        locked_commit = str(entry["commit"])
        row: dict[str, Any] = {
            "agent_id": agent_id,
            "path": str(target),
            "locked_commit": locked_commit,
            "ref": entry.get("ref"),
            "repo": entry.get("repo"),
        }
        if not target.exists():
            row["status"] = "missing"
            rows.append(row)
            continue
        if not is_git_worktree(target):
            row["status"] = "not_git"
            rows.append(row)
            continue
        current = current_commit(target)
        row.update(
            {
                "status": "locked" if current == locked_commit else "drifted",
                "current_commit": current,
                "branch": current_branch(target),
                "dirty": dirty_state(target),
                "symlink": target.is_symlink(),
            }
        )
        row.update(ahead_behind(target, locked_commit))
        rows.append(row)
    return rows


def remote_commit(repo: str, ref: str | None) -> str:
    query_ref = ref or "HEAD"
    result = run_git(["ls-remote", repo, query_ref], check=True)
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines and ref:
        result = run_git(["ls-remote", repo, f"refs/heads/{ref}"], check=True)
        lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise AgentLockError(f"could not resolve remote ref {query_ref} for {repo}")
    return lines[0].split()[0]


def update_lock(lock_path: Path, agents_dir: Path) -> dict[str, Any]:
    lock = read_lock(lock_path)
    updated = {"version": lock.get("version", 1), "agents": {}}
    for agent_id, entry in lock["agents"].items():
        target = agents_dir / agent_id
        repo = str(entry["repo"])
        ref = str(entry.get("ref") or "")
        commit: str
        if target.exists() and is_git_worktree(target):
            branch = current_branch(target) or ref
            if branch:
                run_git(["-C", str(target), "fetch", "origin", branch], check=False)
                candidate = run_git(["-C", str(target), "rev-parse", f"origin/{branch}"], check=False)
                commit = candidate.stdout.strip() if candidate.returncode == 0 else current_commit(target) or ""
                ref = branch
            else:
                commit = current_commit(target) or ""
        else:
            commit = remote_commit(repo, ref or None)
        if not commit:
            raise AgentLockError(f"{agent_id}: could not determine update-lock commit")
        updated["agents"][agent_id] = {"repo": repo, "ref": ref or None, "commit": commit}
    write_lock(lock_path, updated)
    return updated


def print_human_status(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        agent_id = row["agent_id"]
        status = row["status"]
        if status == "missing":
            print(f"missing  {agent_id}: not cloned")
            continue
        if status == "not_git":
            print(f"error    {agent_id}: path exists but is not git")
            continue
        marker = "locked" if status == "locked" and row.get("dirty") == "clean" else status
        suffix = " symlink" if row.get("symlink") else ""
        branch = row.get("branch") or "detached"
        current = str(row.get("current_commit") or "")[:12]
        locked = str(row.get("locked_commit") or "")[:12]
        ahead = row.get("ahead")
        behind = row.get("behind")
        drift = "" if status == "locked" else f" lock={locked} ahead={ahead} behind={behind}"
        dirty = "" if row.get("dirty") == "clean" else f" {row.get('dirty')}"
        print(f"{marker:<8} {agent_id} ({branch}) {current}{drift}{dirty}{suffix}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage subordinate agent lockfile checkouts.")
    parser.add_argument("command", choices=("sync", "status", "update-lock"))
    parser.add_argument("--lock", type=Path, default=Path("agents.lock"))
    parser.add_argument("--agents-dir", type=Path, default=Path("agents"))
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    try:
        if args.command == "sync":
            payload: Any = sync_agents(args.lock, args.agents_dir)
        elif args.command == "status":
            payload = status_agents(args.lock, args.agents_dir)
        else:
            payload = update_lock(args.lock, args.agents_dir)
    except AgentLockError as exc:
        print(f"agent-lock: {exc}", file=sys.stderr)
        return 1

    if args.json or args.command != "status":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_human_status(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
