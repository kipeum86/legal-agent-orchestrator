from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI = REPO_ROOT / "scripts" / "acceptance-check.py"


def load_acceptance_module():
    spec = importlib.util.spec_from_file_location("acceptance_check", CLI)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {CLI}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AcceptanceCheckTests(unittest.TestCase):
    def test_acceptance_check_passes_all_criteria_as_json(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CLI), "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["passed"])
        self.assertEqual(payload["total"], 15)
        self.assertEqual(payload["passed_count"], 15)

    def test_acceptance_check_writes_markdown_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "acceptance.md"
            result = subprocess.run(
                [sys.executable, str(CLI), "--write", str(report)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            text = report.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Status: PASS (15/15 criteria)", text)
        self.assertIn("Pattern 3 transcript", text)
        self.assertIn("MCP pinning", text)

    def test_run_checks_reports_checker_exceptions_as_failures(self) -> None:
        module = load_acceptance_module()

        def broken_check():
            raise RuntimeError("boom")

        original_checks = module.CHECKS
        try:
            module.CHECKS = (broken_check,)
            results = module.run_checks()
        finally:
            module.CHECKS = original_checks

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)
        self.assertIn("RuntimeError: boom", results[0].evidence[0])


if __name__ == "__main__":
    unittest.main()
