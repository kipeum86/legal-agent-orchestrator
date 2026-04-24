from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI = REPO_ROOT / "scripts" / "agent-lock.py"


def run(command: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=cwd)


def commit_file(repo: Path, filename: str, text: str) -> str:
    (repo / filename).write_text(text, encoding="utf-8")
    git(repo, "add", filename)
    git(repo, "commit", "-m", f"Update {filename}")
    return git(repo, "rev-parse", "HEAD").stdout.strip()


class AgentLockTests(unittest.TestCase):
    def make_source_repo(self, root: Path) -> tuple[Path, str, str]:
        source = root / "source-agent"
        source.mkdir()
        git(source, "init")
        git(source, "checkout", "-b", "main")
        git(source, "config", "user.email", "agent-lock@example.test")
        git(source, "config", "user.name", "Agent Lock Test")
        first = commit_file(source, "README.md", "first\n")
        second = commit_file(source, "README.md", "second\n")
        return source, first, second

    def write_lock(self, path: Path, repo: Path, commit: str) -> None:
        payload = {
            "version": 1,
            "agents": {
                "source-agent": {
                    "repo": str(repo),
                    "ref": "main",
                    "commit": commit,
                }
            },
        }
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def test_sync_checks_out_locked_commit_and_status_reports_locked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, first, _ = self.make_source_repo(root)
            lock = root / "agents.lock"
            agents_dir = root / "agents"
            self.write_lock(lock, source, first)

            sync = run(
                [
                    sys.executable,
                    str(CLI),
                    "sync",
                    "--lock",
                    str(lock),
                    "--agents-dir",
                    str(agents_dir),
                ]
            )
            status = run(
                [
                    sys.executable,
                    str(CLI),
                    "status",
                    "--json",
                    "--lock",
                    str(lock),
                    "--agents-dir",
                    str(agents_dir),
                ]
            )

        self.assertIn("source-agent", sync.stdout)
        rows = json.loads(status.stdout)
        self.assertEqual(rows[0]["status"], "locked")
        self.assertEqual(rows[0]["current_commit"], first)

    def test_update_lock_moves_to_remote_ref_commit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, first, second = self.make_source_repo(root)
            lock = root / "agents.lock"
            agents_dir = root / "agents"
            self.write_lock(lock, source, first)

            run(
                [
                    sys.executable,
                    str(CLI),
                    "sync",
                    "--lock",
                    str(lock),
                    "--agents-dir",
                    str(agents_dir),
                ]
            )
            run(
                [
                    sys.executable,
                    str(CLI),
                    "update-lock",
                    "--lock",
                    str(lock),
                    "--agents-dir",
                    str(agents_dir),
                ]
            )
            payload = json.loads(lock.read_text(encoding="utf-8"))

        self.assertEqual(payload["agents"]["source-agent"]["commit"], second)


if __name__ == "__main__":
    unittest.main()
