#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib.cli import load_payload
from scripts.lib.routing import select_route


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Select an orchestrator route from classification JSON.")
    parser.add_argument("classification_json", nargs="?", type=Path)
    args = parser.parse_args(argv)

    try:
        route = select_route(load_payload(args.classification_json, label="classification input"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"select-route: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(route, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
