# MCP Version Changelog

This file records intentional MCP package pin changes for `.mcp.json`.

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
