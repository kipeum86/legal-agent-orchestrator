from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI = REPO_ROOT / "scripts" / "sync-agents.py"
sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.agent_sync import format_timestamp, sync_agents  # noqa: E402

NOW = datetime(2026, 5, 27, 10, 15, tzinfo=timezone.utc)


class SyncAgentsTests(unittest.TestCase):
    def write_fake_setup(self, root: Path, *, exit_code: int = 0) -> tuple[Path, Path]:
        setup = root / "fake-setup.sh"
        log_path = root / "setup.log"
        setup.write_text(
            f"""#!/bin/sh
set -eu
printf '%s\\n' "$*" >> "$FAKE_SETUP_LOG"
if [ "$#" -gt 0 ]; then
  shift
fi
if [ "${{FAKE_SETUP_CREATE_CHECKOUTS:-1}}" = "1" ]; then
  for target in "$@"; do
    mkdir -p "$AGENTS_DIR/$target/.git"
  done
fi
exit {exit_code}
""",
            encoding="utf-8",
        )
        setup.chmod(0o755)
        return setup, log_path

    def write_state(self, path: Path, agent_id: str, last_success: datetime) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "default_branch": "main",
                    "agents": {
                        agent_id: {
                            "last_attempt_at": format_timestamp(last_success),
                            "last_success_at": format_timestamp(last_success),
                            "status": "ok",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

    def test_ttl_skips_recent_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            agents_dir = root / "agents"
            (agents_dir / "legal-research-agent" / ".git").mkdir(parents=True)
            state_path = agents_dir / ".sync-state.json"
            self.write_state(state_path, "legal-research-agent", NOW - timedelta(seconds=30))

            result, exit_code = sync_agents(
                ["legal-research-agent"],
                repo_root=root,
                agents_dir=agents_dir,
                state_path=state_path,
                setup_script=root / "missing-setup.sh",
                env={"LEGAL_ORCHESTRATOR_AGENT_SYNC_TTL_SECONDS": "600"},
                now=NOW,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["skipped"], [{"agent_id": "legal-research-agent", "reason": "ttl"}])

    def test_missing_checkout_syncs_even_with_fresh_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            agents_dir = root / "agents"
            state_path = agents_dir / ".sync-state.json"
            self.write_state(state_path, "legal-research-agent", NOW)
            setup, log_path = self.write_fake_setup(root)

            result, exit_code = sync_agents(
                ["legal-research-agent"],
                repo_root=root,
                agents_dir=agents_dir,
                state_path=state_path,
                setup_script=setup,
                env={
                    "FAKE_SETUP_LOG": str(log_path),
                    "AGENTS_DIR": str(agents_dir),
                    "LEGAL_ORCHESTRATOR_AGENT_SYNC_TTL_SECONDS": "600",
                },
                now=NOW,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["synced"], ["legal-research-agent"])
            self.assertIn("update legal-research-agent", log_path.read_text(encoding="utf-8"))

    def test_force_sync_overrides_ttl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            agents_dir = root / "agents"
            (agents_dir / "legal-research-agent" / ".git").mkdir(parents=True)
            state_path = agents_dir / ".sync-state.json"
            self.write_state(state_path, "legal-research-agent", NOW)
            setup, log_path = self.write_fake_setup(root)

            result, exit_code = sync_agents(
                ["legal-research-agent"],
                repo_root=root,
                agents_dir=agents_dir,
                state_path=state_path,
                setup_script=setup,
                env={
                    "FAKE_SETUP_LOG": str(log_path),
                    "AGENTS_DIR": str(agents_dir),
                    "LEGAL_ORCHESTRATOR_FORCE_AGENT_SYNC": "1",
                },
                now=NOW,
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(result["force"])
            self.assertEqual(result["synced"], ["legal-research-agent"])

    def test_env_skip_overrides_missing_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            agents_dir = root / "agents"

            result, exit_code = sync_agents(
                ["legal-research-agent"],
                repo_root=root,
                agents_dir=agents_dir,
                state_path=agents_dir / ".sync-state.json",
                setup_script=root / "missing-setup.sh",
                env={"LEGAL_ORCHESTRATOR_SKIP_AGENT_SYNC": "1"},
                now=NOW,
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(result["skip"])
            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["skipped"], [{"agent_id": "legal-research-agent", "reason": "env_skip"}])

    def test_symlink_checkout_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            agents_dir = root / "agents"
            agents_dir.mkdir()
            dev_checkout = root / "dev-agent"
            dev_checkout.mkdir()
            (agents_dir / "legal-research-agent").symlink_to(dev_checkout)

            result, exit_code = sync_agents(
                ["legal-research-agent"],
                repo_root=root,
                agents_dir=agents_dir,
                state_path=agents_dir / ".sync-state.json",
                setup_script=root / "missing-setup.sh",
                now=NOW,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["skipped"], [{"agent_id": "legal-research-agent", "reason": "symlink"}])

    def test_ttl_zero_disables_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            agents_dir = root / "agents"
            (agents_dir / "legal-research-agent" / ".git").mkdir(parents=True)
            state_path = agents_dir / ".sync-state.json"
            self.write_state(state_path, "legal-research-agent", NOW)
            setup, log_path = self.write_fake_setup(root)

            result, exit_code = sync_agents(
                ["legal-research-agent"],
                repo_root=root,
                agents_dir=agents_dir,
                state_path=state_path,
                setup_script=setup,
                env={
                    "FAKE_SETUP_LOG": str(log_path),
                    "AGENTS_DIR": str(agents_dir),
                    "LEGAL_ORCHESTRATOR_AGENT_SYNC_TTL_SECONDS": "0",
                },
                now=NOW,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["synced"], ["legal-research-agent"])

    def test_failed_sync_is_recoverable_when_checkout_exists(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            agents_dir = root / "agents"
            (agents_dir / "legal-research-agent" / ".git").mkdir(parents=True)
            setup, log_path = self.write_fake_setup(root, exit_code=1)

            result, exit_code = sync_agents(
                ["legal-research-agent"],
                repo_root=root,
                agents_dir=agents_dir,
                state_path=agents_dir / ".sync-state.json",
                setup_script=setup,
                env={
                    "FAKE_SETUP_LOG": str(log_path),
                    "AGENTS_DIR": str(agents_dir),
                },
                now=NOW,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(result["status"], "failed")
            self.assertTrue(result["recoverable"])
            self.assertEqual(result["fallback"], "cached_versions")

    def test_failed_sync_is_unrecoverable_when_checkout_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            agents_dir = root / "agents"
            setup, log_path = self.write_fake_setup(root, exit_code=1)

            result, exit_code = sync_agents(
                ["legal-research-agent"],
                repo_root=root,
                agents_dir=agents_dir,
                state_path=agents_dir / ".sync-state.json",
                setup_script=setup,
                env={
                    "FAKE_SETUP_LOG": str(log_path),
                    "AGENTS_DIR": str(agents_dir),
                    "FAKE_SETUP_CREATE_CHECKOUTS": "0",
                },
                now=NOW,
            )

            self.assertEqual(exit_code, 1)
            self.assertEqual(result["status"], "failed")
            self.assertFalse(result["recoverable"])

    def test_retired_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "retired agent/repo ID"):
                sync_agents(["PIPA-expert"], repo_root=root)

    def test_cli_reads_targets_file_and_prints_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            agents_dir = root / "agents"
            targets = root / "targets.json"
            targets.write_text(json.dumps(["legal-research-agent"]), encoding="utf-8")
            setup, log_path = self.write_fake_setup(root)

            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "--repo-root",
                    str(root),
                    "--agents-dir",
                    str(agents_dir),
                    "--state-file",
                    str(agents_dir / ".sync-state.json"),
                    "--setup-script",
                    str(setup),
                    "--targets-file",
                    str(targets),
                    "--now",
                    "2026-05-27T10:15:00Z",
                    "--json",
                ],
                cwd=REPO_ROOT,
                env={
                    **os.environ,
                    "FAKE_SETUP_LOG": str(log_path),
                    "AGENTS_DIR": str(agents_dir),
                },
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["synced"], ["legal-research-agent"])

    def test_cli_rejects_bad_targets_file_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            targets = root / "targets.json"
            targets.write_text(json.dumps({"agent": "legal-research-agent"}), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(CLI), "--targets-file", str(targets), "--json"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("targets file must contain a JSON array", result.stderr)


if __name__ == "__main__":
    unittest.main()
