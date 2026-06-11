# MCP Version Changelog

This file records intentional MCP package pin changes for `.mcp.json`.

## 2026-06-11

Updated exact MCP package pins after GitHub issue #2 reported newer npm releases:

| MCP server | Package | Previous pin | New pin | Verification |
|---|---|---:|---:|---|
| `korean-law` | `korean-law-mcp` | `4.0.6` | `4.4.1` | `npm view korean-law-mcp version` returned `4.4.1` |
| `kordoc` | `kordoc` | `2.9.0` | `3.0.1` | `npm view kordoc version` returned `3.0.1` |

Smoke:
- `python3 scripts/check-mcp-pins.py .mcp.json --json`
- `python3 -m pytest`
- `python3 scripts/sanitize-check.py --self-test`
- `python3 scripts/smoke-check.py`
- `python3 scripts/acceptance-check.py --json`

Notes:
- Issue #2 (2026-06-01) flagged `korean-law-mcp` `4.0.7`; upstream released several newer versions before this bump, so the pin goes straight to the current latest `4.4.1` (four releases shipped on 2026-06-11 alone — watch first live lookups for churn-related regressions).
- `kordoc` crossed a major version boundary (`2.x` to `3.x`) and was not flagged by issue #2 because `3.0.1` shipped after the issue was created.
- Live legal-source MCP queries were not run in this pinning milestone because they require runtime credentials and user case context.

## 2026-05-26

Updated exact MCP package pins after GitHub issue #1 reported newer npm releases:

| MCP server | Package | Previous pin | New pin | Verification |
|---|---|---:|---:|---|
| `korean-law` | `korean-law-mcp` | `3.5.4` | `4.0.6` | `npm view korean-law-mcp version --json` returned `4.0.6` |
| `kordoc` | `kordoc` | `2.5.2` | `2.9.0` | `npm view kordoc version --json` returned `2.9.0` |

Smoke:
- `python3 scripts/check-mcp-pins.py .mcp.json --json`
- `python3 -m pytest`
- `python3 scripts/sanitize-check.py --self-test`
- `python3 scripts/smoke-check.py`
- `python3 scripts/acceptance-check.py --json`

Notes:
- Live legal-source MCP queries were not run in this pinning milestone because they require runtime credentials and user case context.
- `korean-law-mcp` crossed a major version boundary (`3.x` to `4.x`), so downstream case execution should keep an eye on first live statute/precedent lookups.

## 2026-04-24

Initial exact-version pinning:

| MCP server | Package | Pinned version | Verification |
|---|---|---:|---|
| `korean-law` | `korean-law-mcp` | `3.5.4` | `npm view korean-law-mcp version --json` returned `3.5.4` |
| `kordoc` | `kordoc` | `2.5.2` | `npm view kordoc version --json` returned `2.5.2` |

Smoke:
- `python3 scripts/check-mcp-pins.py .mcp.json --json`
- `python3 -m unittest tests.test_mcp_pins`

Notes:
- Live legal-source MCP queries were not run in this pinning milestone because they require runtime credentials and user case context.
- Future pin bumps should record the package version, reason for bump, and smoke result here before merging.
