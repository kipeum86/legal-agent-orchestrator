from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI = REPO_ROOT / "scripts" / "check-mcp-pins.py"


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
        self.assertEqual(specs["korean-law"], "korean-law-mcp@3.5.4")
        self.assertEqual(specs["kordoc"], "kordoc@2.5.2")

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
                                "version": "3.5.4",
                                "latest": "3.5.5",
                                "update_available": True,
                            },
                            {
                                "server": "kordoc",
                                "package": "kordoc",
                                "version": "2.5.2",
                                "latest": "2.5.2",
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


if __name__ == "__main__":
    unittest.main()
