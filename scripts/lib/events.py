from __future__ import annotations

import fcntl
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVENT_ID_RE = re.compile(r"^evt_(\d{3,})$")
EVENT_ID_FRAGMENT_RE = re.compile(r'"id"\s*:\s*"evt_(\d{3,})"')
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
                fragment = EVENT_ID_FRAGMENT_RE.search(line)
                if fragment:
                    max_seen = max(max_seen, int(fragment.group(1)))
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
        encoded = (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        with event_path.open("ab+") as handle:
            handle.seek(0, 2)
            if handle.tell() > 0:
                handle.seek(handle.tell() - 1)
                if handle.read(1) != b"\n":
                    handle.write(b"\n")
            handle.write(encoded)
        return event
    finally:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        lock_handle.close()
