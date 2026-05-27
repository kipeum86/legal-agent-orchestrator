#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib.agent_sync import parse_timestamp, read_targets, sync_agents


def load_targets(args: argparse.Namespace) -> list[str]:
    if args.targets_file is not None:
        if args.targets:
            raise ValueError("pass either --targets-file or positional agent IDs, not both")
        return read_targets(args.targets_file)
    return [str(target) for target in args.targets]


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Sync selected subordinate agents with TTL caching.")
    parser.add_argument("targets", nargs="*", help="Agent IDs to sync.")
    parser.add_argument("--targets-file", type=Path, help="JSON array of agent IDs to sync.")
    parser.add_argument("--agents-dir", type=Path, default=repo_root / "agents")
    parser.add_argument("--state-file", type=Path, default=None)
    parser.add_argument("--setup-script", type=Path, default=repo_root / "setup.sh")
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument("--now", help="UTC timestamp override for tests, e.g. 2026-05-27T10:15:00Z.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    try:
        now = parse_timestamp(args.now) if args.now else None
        if args.now and now is None:
            raise ValueError("--now must be an ISO timestamp")
        result, exit_code = sync_agents(
            load_targets(args),
            repo_root=args.repo_root,
            agents_dir=args.agents_dir,
            state_path=args.state_file,
            setup_script=args.setup_script,
            now=now,
            dry_run=args.dry_run,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"sync-agents: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = result.get("status", "unknown")
        targets = ", ".join(result.get("targets", [])) or "(none)"
        print(f"sync-agents: {status} targets={targets}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
