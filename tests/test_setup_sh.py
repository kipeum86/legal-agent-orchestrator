from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SETUP_SH = REPO_ROOT / "setup.sh"


class SetupShTests(unittest.TestCase):
    def copy_setup(self, directory: Path) -> Path:
        script = directory / "setup.sh"
        shutil.copy2(SETUP_SH, script)
        return script

    def write_fake_git(self, directory: Path) -> Path:
        bin_dir = directory / "bin"
        bin_dir.mkdir()
        fake_git = bin_dir / "git"
        fake_git.write_text(
            """#!/bin/sh
set -eu
printf '%s\\n' "$*" >> "$FAKE_GIT_LOG"

if [ "${1:-}" = "-C" ]; then
  shift
  shift
fi

cmd="${1:-}"
shift || true

case "$cmd" in
  fetch)
    exit 0
    ;;
  rev-parse)
    echo "same-sha"
    exit 0
    ;;
  status)
    if [ "${FAKE_GIT_DIRTY:-0}" = "1" ]; then
      echo " M tracked-file"
    fi
    exit 0
    ;;
  reset)
    echo "reset-ok"
    exit 0
    ;;
  clone)
    target=""
    for arg in "$@"; do
      target="$arg"
    done
    mkdir -p "$target/.git"
    exit 0
    ;;
  ls-remote)
    echo "same-sha refs/heads/main"
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
""",
            encoding="utf-8",
        )
        fake_git.chmod(0o755)
        return bin_dir

    def run_setup(
        self,
        script: Path,
        *args: str,
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        return subprocess.run(
            ["bash", str(script), *args],
            cwd=cwd,
            env=merged_env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_unknown_agent_id_fails_before_creating_agents_dir(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = self.copy_setup(root)

            result = self.run_setup(script, "update", "unknown-agent", cwd=root)

            self.assertEqual(result.returncode, 2)
            self.assertIn("Unknown agent id: unknown-agent", result.stderr)
            self.assertFalse((root / "agents").exists())

    def test_update_accepts_selected_agent_and_skips_reset_when_clean(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = self.copy_setup(root)
            bin_dir = self.write_fake_git(root)
            checkout = root / "agents" / "legal-research-agent" / ".git"
            checkout.mkdir(parents=True)
            log_path = root / "git.log"

            result = self.run_setup(
                script,
                "update",
                "legal-research-agent",
                cwd=root,
                env={
                    "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                    "FAKE_GIT_LOG": str(log_path),
                },
            )
            calls = log_path.read_text(encoding="utf-8")

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("legal-research-agent already at latest main", result.stdout)
            self.assertIn("Selected subordinate agents", result.stdout)
            self.assertIn("fetch --depth 1 origin main", calls)
            self.assertNotIn("reset --hard", calls)
            self.assertNotIn("data-protection-agent", calls)

    def test_update_resets_selected_agent_when_tracked_tree_is_dirty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = self.copy_setup(root)
            bin_dir = self.write_fake_git(root)
            checkout = root / "agents" / "legal-research-agent" / ".git"
            checkout.mkdir(parents=True)
            log_path = root / "git.log"

            result = self.run_setup(
                script,
                "update",
                "legal-research-agent",
                cwd=root,
                env={
                    "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                    "FAKE_GIT_LOG": str(log_path),
                    "FAKE_GIT_DIRTY": "1",
                },
            )
            calls = log_path.read_text(encoding="utf-8")

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("legal-research-agent synced to latest main", result.stdout)
            self.assertIn("reset --hard origin/main", calls)


if __name__ == "__main__":
    unittest.main()
