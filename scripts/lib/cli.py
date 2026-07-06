from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def load_payload(path: Path | None, *, label: str = "input") -> dict[str, Any]:
    raw = sys.stdin.read() if path is None else path.read_text(encoding="utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload
