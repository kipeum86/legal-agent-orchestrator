#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib.sync_targets import resolve_sync_targets


def load_payload(path: Path | None) -> dict:
    raw = sys.stdin.read() if path is None else path.read_text(encoding="utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("route input must be a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve subordinate agents to sync from route-selection JSON.")
    parser.add_argument("route_json", nargs="?", type=Path)
    args = parser.parse_args(argv)

    try:
        targets = resolve_sync_targets(load_payload(args.route_json))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"resolve-sync-targets: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(targets, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
