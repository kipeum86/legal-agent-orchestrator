#!/usr/bin/env python3
"""Append one validated JSON event to an events.jsonl file.

The writer owns event-id assignment under a file lock so parallel orchestration
steps cannot create duplicate evt_### identifiers.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVENT_ID_RE = re.compile(r"^evt_(\d{3,})$")
LOCK_TIMEOUT_SECONDS = 10.0


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_data(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--data-json is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("--data-json must decode to an object")
    return payload


def next_event_id(path: Path) -> str:
    max_seen = 0
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            match = EVENT_ID_RE.match(str(payload.get("id") or ""))
            if match:
                max_seen = max(max_seen, int(match.group(1)))
    return f"evt_{max_seen + 1:03d}"


def acquire_lock(lock_path: Path):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("w", encoding="utf-8")
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    while True:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return handle
        except BlockingIOError:
            if time.monotonic() >= deadline:
                handle.close()
                raise TimeoutError(f"timed out waiting for lock: {lock_path}")
            time.sleep(0.05)


def append_event(
    event_path: Path,
    *,
    agent: str,
    event_type: str,
    data: dict[str, Any],
    event_id: str = "auto",
    final: bool = False,
    timestamp: str | None = None,
) -> dict[str, Any]:
    event_path.parent.mkdir(parents=True, exist_ok=True)
    lock_handle = acquire_lock(event_path.with_suffix(event_path.suffix + ".lock"))
    try:
        if final:
            resolved_id = "evt_final"
        elif event_id == "auto":
            if event_type == "final_output":
                raise ValueError("final_output events must be written with --final")
            resolved_id = next_event_id(event_path)
        else:
            resolved_id = event_id

        event = {
            "id": resolved_id,
            "ts": timestamp or utc_now(),
            "agent": agent,
            "type": event_type,
            "data": data,
        }
        with event_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
        return event
    finally:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        lock_handle.close()


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
