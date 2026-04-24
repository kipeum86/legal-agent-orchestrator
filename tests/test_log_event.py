from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI = REPO_ROOT / "scripts" / "log-event.py"


def run_log_event(events_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), str(events_path), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class LogEventCliTests(unittest.TestCase):
    def test_rejects_invalid_data_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_log_event(
                Path(directory) / "events.jsonl",
                "--agent",
                "orchestrator",
                "--type",
                "case_received",
                "--data-json",
                "{bad-json",
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("not valid JSON", result.stderr)

    def test_preserves_escaped_payload_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            events_path = Path(directory) / "events.jsonl"
            query = 'line "quoted"\nnext'
            result = run_log_event(
                events_path,
                "--agent",
                "orchestrator",
                "--type",
                "case_received",
                "--data-json",
                json.dumps({"query": query}, ensure_ascii=False),
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            event = json.loads(events_path.read_text(encoding="utf-8"))
            self.assertEqual(event["id"], "evt_001")
            self.assertEqual(event["data"]["query"], query)

    def test_final_output_requires_final_flag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            events_path = Path(directory) / "events.jsonl"
            result = run_log_event(
                events_path,
                "--agent",
                "orchestrator",
                "--type",
                "final_output",
                "--data-json",
                "{}",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("--final", result.stderr)

            final_result = run_log_event(
                events_path,
                "--agent",
                "orchestrator",
                "--type",
                "final_output",
                "--final",
                "--data-json",
                "{}",
            )

            self.assertEqual(final_result.returncode, 0, msg=final_result.stderr)
            event = json.loads(events_path.read_text(encoding="utf-8"))
            self.assertEqual(event["id"], "evt_final")

    def test_parallel_writes_get_unique_monotonic_event_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            events_path = Path(directory) / "events.jsonl"

            def write_event(index: int) -> subprocess.CompletedProcess[str]:
                return run_log_event(
                    events_path,
                    "--agent",
                    "worker",
                    "--type",
                    "agent_completed",
                    "--data-json",
                    json.dumps({"index": index}),
                )

            with ThreadPoolExecutor(max_workers=8) as executor:
                results = list(executor.map(write_event, range(20)))

            failures = [result.stderr for result in results if result.returncode != 0]
            self.assertEqual(failures, [])
            events = [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            ids = sorted(event["id"] for event in events)
            self.assertEqual(len(ids), 20)
            self.assertEqual(ids, [f"evt_{index:03d}" for index in range(1, 21)])


if __name__ == "__main__":
    unittest.main()
