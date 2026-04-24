#!/usr/bin/env python3
"""Run repository smoke checks that are safe for a clean working tree."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PATTERN2_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "cases" / "pattern2-basic"
PATTERN1_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "cases" / "pattern1-multi-agent"


def run_step(name: str, command: list[str], *, cwd: Path = REPO_ROOT) -> None:
    print(f"[smoke] {name}")
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        raise SystemExit(result.returncode)


def run_smoke_checks() -> None:
    run_step("sanitize self-test", [sys.executable, "scripts/sanitize-check.py", "--self-test"])
    run_step("validate pattern2 fixture", [sys.executable, "scripts/validate-case.py", str(PATTERN2_FIXTURE), "--mode", "strict"])
    run_step("validate pattern1 fixture", [sys.executable, "scripts/validate-case.py", str(PATTERN1_FIXTURE), "--mode", "strict"])
    run_step("validate MCP pins", [sys.executable, "scripts/check-mcp-pins.py", ".mcp.json", "--json"])

    with tempfile.TemporaryDirectory(prefix="legal-orchestrator-smoke-") as directory:
        case_dir = Path(directory) / "pattern2-basic"
        shutil.copytree(PATTERN2_FIXTURE, case_dir)
        run_step(
            "generate case report from pattern2 fixture copy",
            [sys.executable, "scripts/generate-case-report.py", str(case_dir)],
        )
        report = case_dir / "case-report.md"
        if not report.exists():
            raise SystemExit("smoke-check: case-report.md was not generated")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run clean-tree smoke checks.")
    parser.parse_args(argv)
    run_smoke_checks()
    print("[smoke] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
