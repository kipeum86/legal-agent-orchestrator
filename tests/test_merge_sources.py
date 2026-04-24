from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI = REPO_ROOT / "scripts" / "merge-sources.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "cases" / "pattern1-multi-agent"


class MergeSourcesTests(unittest.TestCase):
    def test_merges_multi_agent_meta_and_events_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            shutil.copytree(FIXTURE, case_dir)
            result = subprocess.run(
                [sys.executable, str(CLI), str(case_dir)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads((case_dir / "sources.json").read_text(encoding="utf-8"))

        self.assertEqual(payload["total_sources"], 2)
        self.assertEqual(payload["grade_distribution"], {"A": 2, "B": 0, "C": 0, "D": 0})
        agents = {agent["agent_id"]: agent for agent in payload["agents"]}
        self.assertEqual(set(agents), {"GDPR-expert", "PIPA-expert"})
        self.assertEqual(agents["PIPA-expert"]["sources"][0]["citation"], "제28조의8")
        self.assertEqual(agents["GDPR-expert"]["sources"][0]["citation"], "Article 28")


if __name__ == "__main__":
    unittest.main()
