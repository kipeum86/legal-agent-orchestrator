from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI = REPO_ROOT / "scripts" / "check-mcp-pins.py"


def load_mcp_module():
    spec = importlib.util.spec_from_file_location("check_mcp_pins", CLI)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {CLI}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class McpPinTests(unittest.TestCase):
    def test_repo_mcp_config_has_exact_pins(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CLI), str(REPO_ROOT / ".mcp.json"), "--json"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        specs = {item["server"]: item["spec"] for item in payload["packages"]}
        self.assertEqual(specs["korean-law"], "korean-law-mcp@4.4.1")
        self.assertEqual(specs["kordoc"], "kordoc@3.0.1")

    def test_latest_and_bare_specs_fail_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / ".mcp.json"
            config.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "latest": {"command": "npx", "args": ["-y", "pkg@latest"]},
                            "bare": {"command": "npx", "args": ["-y", "kordoc"]},
                        }
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(CLI), str(config)],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("uses @latest", result.stderr)
        self.assertIn("has no explicit version", result.stderr)

    def test_markdown_report_only_mentions_updates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.json"
            report.write_text(
                json.dumps(
                    {
                        "packages": [
                            {
                                "server": "korean-law",
                                "package": "korean-law-mcp",
                                "version": "4.0.5",
                                "latest": "4.0.6",
                                "update_available": True,
                            },
                            {
                                "server": "kordoc",
                                "package": "kordoc",
                                "version": "2.9.0",
                                "latest": "2.9.0",
                                "update_available": False,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(CLI), "--markdown-report", str(report)],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("korean-law-mcp", result.stdout)
        self.assertNotIn("| `kordoc` |", result.stdout)

    def test_latest_report_preserves_pin_order(self) -> None:
        module = load_mcp_module()
        latest_by_package = {"pkg-a": "1.0.1", "pkg-b": "2.0.0", "pkg-c": "3.1.0"}
        original = module.npm_latest
        try:
            module.npm_latest = lambda package: latest_by_package[package]
            report = module.latest_report(
                [
                    {"server": "a", "package": "pkg-a", "version": "1.0.0", "spec": "pkg-a@1.0.0"},
                    {"server": "b", "package": "pkg-b", "version": "2.0.0", "spec": "pkg-b@2.0.0"},
                    {"server": "c", "package": "pkg-c", "version": "3.0.0", "spec": "pkg-c@3.0.0"},
                ]
            )
        finally:
            module.npm_latest = original

        self.assertEqual([item["package"] for item in report["packages"]], ["pkg-a", "pkg-b", "pkg-c"])
        self.assertEqual([item["update_available"] for item in report["packages"]], [True, False, True])


if __name__ == "__main__":
    unittest.main()
