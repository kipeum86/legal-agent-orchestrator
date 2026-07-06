#!/usr/bin/env python3
"""Append one validated JSON event to an events.jsonl file.

The writer owns event-id assignment under a file lock so parallel orchestration
steps cannot create duplicate evt_### identifiers.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib.events import append_event, load_data  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Append an orchestrator event to events.jsonl.")
    parser.add_argument("events_path", type=Path)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--type", dest="event_type", required=True)
    parser.add_argument("--data-json", default="{}")
    parser.add_argument("--event-id", default="auto")
    parser.add_argument("--ts", default=None)
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args(argv)

    try:
        data = load_data(args.data_json)
        event = append_event(
            args.events_path,
            agent=args.agent,
            event_type=args.event_type,
            data=data,
            event_id=args.event_id,
            final=args.final,
            timestamp=args.ts,
        )
    except (TimeoutError, ValueError) as exc:
        print(f"log-event: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(event, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
