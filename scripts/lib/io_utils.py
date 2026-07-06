from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def read_json(path: Path) -> Any | None:
    text = read_text(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    text = read_text(path)
    if text is None:
        return []
    events: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def parse_jsonl_strict(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    text = read_text(path)
    if text is None:
        return [], [f"missing events file: {path.name}"]

    events: list[dict[str, Any]] = []
    for index, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"events.jsonl:{index}: invalid JSON: {exc}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"events.jsonl:{index}: event must be an object")
            continue
        events.append(payload)
    return events, errors
