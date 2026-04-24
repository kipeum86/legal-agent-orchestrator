#!/usr/bin/env python3
"""Validate and monitor pinned MCP npm package versions."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

PACKAGE_RE = re.compile(
    r"^(?P<name>(?:@[A-Za-z0-9_.-]+/)?[A-Za-z0-9_.-]+)@(?P<version>\d+\.\d+\.\d+(?:[-+][A-Za-z0-9_.-]+)?)$"
)


class McpPinError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise McpPinError(f"cannot read {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise McpPinError(f"{path}: expected JSON object")
    return payload


def package_specs(config: dict[str, Any]) -> list[dict[str, str]]:
    servers = config.get("mcpServers")
    if not isinstance(servers, dict):
        raise McpPinError("mcpServers must be an object")

    specs: list[dict[str, str]] = []
    for server_name, server in sorted(servers.items()):
        if not isinstance(server, dict):
            raise McpPinError(f"{server_name}: server config must be an object")
        command = str(server.get("command") or "")
        args = server.get("args")
        if command != "npx":
            continue
        if not isinstance(args, list):
            raise McpPinError(f"{server_name}: npx args must be an array")
        for arg in args:
            value = str(arg)
            if value.startswith("-"):
                continue
            specs.append({"server": str(server_name), "spec": value})
            break
        else:
            raise McpPinError(f"{server_name}: npx package argument missing")
    return specs


def parse_pinned_spec(spec: str) -> tuple[str, str] | None:
    match = PACKAGE_RE.match(spec)
    if match is None:
        return None
    return match.group("name"), match.group("version")


def validate_pins(config: dict[str, Any]) -> list[dict[str, str]]:
    pins: list[dict[str, str]] = []
    errors: list[str] = []
    for item in package_specs(config):
        spec = item["spec"]
        parsed = parse_pinned_spec(spec)
        if parsed is None:
            if spec.endswith("@latest") or "@latest" in spec:
                errors.append(f"{item['server']}: {spec} uses @latest")
            elif "@" not in spec or spec.startswith("@"):
                errors.append(f"{item['server']}: {spec} has no explicit version")
            else:
                errors.append(f"{item['server']}: {spec} is not pinned to an exact semver")
            continue
        name, version = parsed
        pins.append({"server": item["server"], "package": name, "version": version, "spec": spec})
    if errors:
        raise McpPinError("; ".join(errors))
    return pins


def npm_latest(package: str) -> str:
    try:
        result = subprocess.run(
            ["npm", "view", package, "version", "--json"],
            capture_output=True,
            text=True,
            check=False,
            timeout=45,
        )
    except subprocess.TimeoutExpired as exc:
        raise McpPinError(f"npm view {package} timed out") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise McpPinError(f"npm view {package} failed: {detail}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise McpPinError(f"npm view {package} returned invalid JSON") from exc
    if not isinstance(value, str) or not value:
        raise McpPinError(f"npm view {package} returned no version")
    return value


def latest_report(pins: list[dict[str, str]]) -> dict[str, Any]:
    packages = []
    for pin in pins:
        latest = npm_latest(pin["package"])
        packages.append(
            {
                **pin,
                "latest": latest,
                "update_available": pin["version"] != latest,
            }
        )
    return {"packages": packages, "updates_available": any(item["update_available"] for item in packages)}


def markdown_report(report: dict[str, Any]) -> str:
    packages = report.get("packages")
    if not isinstance(packages, list):
        return "Invalid MCP version report.\n"
    if not any(isinstance(item, dict) and item.get("update_available") for item in packages):
        return ""
    lines = [
        "## MCP package update available",
        "",
        "| MCP server | Package | Pinned | Latest |",
        "|---|---|---:|---:|",
    ]
    for item in packages:
        if not isinstance(item, dict) or not item.get("update_available"):
            continue
        lines.append(
            f"| `{item.get('server')}` | `{item.get('package')}` | `{item.get('version')}` | `{item.get('latest')}` |"
        )
    lines.extend(
        [
            "",
            "Run `./setup.sh status`, update `.mcp.json`, and record the smoke result in `MCP_VERSION_CHANGELOG.md` before merging.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate pinned MCP npm package versions.")
    parser.add_argument("config", type=Path, nargs="?", default=Path(".mcp.json"))
    parser.add_argument("--json", action="store_true", help="Print pinned package JSON.")
    parser.add_argument("--latest-json", action="store_true", help="Query npm and print latest-version JSON.")
    parser.add_argument(
        "--markdown-report",
        type=Path,
        default=None,
        help="Read a latest-version JSON report and print update markdown.",
    )
    args = parser.parse_args(argv)

    try:
        if args.markdown_report is not None:
            report = read_json(args.markdown_report)
            sys.stdout.write(markdown_report(report))
            return 0

        pins = validate_pins(read_json(args.config))
        if args.latest_json:
            print(json.dumps(latest_report(pins), ensure_ascii=False, indent=2))
        elif args.json:
            print(json.dumps({"packages": pins}, ensure_ascii=False, indent=2))
        return 0
    except McpPinError as exc:
        print(f"check-mcp-pins: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
