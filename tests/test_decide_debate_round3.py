from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI = REPO_ROOT / "scripts" / "decide-debate-round3.py"


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


def write_case(case_dir: Path, *, concessions_a: list[str], concessions_b: list[str]) -> None:
    write_json(
        case_dir / "events.jsonl",
        {
            "id": "evt_001",
            "ts": "2026-04-24T00:00:00Z",
            "agent": "orchestrator",
            "type": "debate_initiated",
            "data": {
                "topic": "확률형 아이템 표시 의무",
                "framing": "KR vs EU",
                "participants": ["PIPA-expert", "GDPR-expert"],
                "max_rounds": 3,
                "case_id": case_dir.name,
            },
        },
    )
    write_json(
        case_dir / "debate-round-1-PIPA-expert-meta.json",
        {"key_claims": ["PIPA claim 1", "PIPA claim 2"]},
    )
    write_json(
        case_dir / "debate-round-1-GDPR-expert-meta.json",
        {"key_claims": ["GDPR claim 1", "GDPR claim 2"]},
    )
    write_json(
        case_dir / "debate-round-2-PIPA-expert-meta.json",
        {"rebuts_agent": "GDPR-expert", "conceded_points": concessions_a},
    )
    write_json(
        case_dir / "debate-round-2-GDPR-expert-meta.json",
        {"rebuts_agent": "PIPA-expert", "conceded_points": concessions_b},
    )


class DecideDebateRound3Tests(unittest.TestCase):
    def run_cli(self, case_dir: Path) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, str(CLI), str(case_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return json.loads(result.stdout)

    def test_convergence_skips_round3_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            case_dir.mkdir()
            write_case(
                case_dir,
                concessions_a=["GDPR claim 1"],
                concessions_b=["PIPA claim 1"],
            )

            first = self.run_cli(case_dir)
            second = self.run_cli(case_dir)

        self.assertEqual(first, second)
        self.assertEqual(first["proceed"], False)
        self.assertEqual(first["reason"], "convergence")
        self.assertEqual(first["conceded_ratio"], 0.5)
        self.assertEqual(first["contested_claims"], ["GDPR claim 2", "PIPA claim 2"])

    def test_significant_disagreement_runs_round3(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            case_dir.mkdir()
            write_case(case_dir, concessions_a=[], concessions_b=["PIPA claim 1"])

            payload = self.run_cli(case_dir)

        self.assertEqual(payload["proceed"], True)
        self.assertEqual(payload["reason"], "significant_disagreement")
        self.assertEqual(payload["conceded_ratio"], 0.25)

    def test_missing_or_malformed_meta_falls_back_to_round3(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case_dir = Path(directory) / "case"
            case_dir.mkdir()
            write_case(
                case_dir,
                concessions_a=["GDPR claim 1"],
                concessions_b=["PIPA claim 1"],
            )
            (case_dir / "debate-round-2-GDPR-expert-meta.json").write_text(
                "{not json",
                encoding="utf-8",
            )

            payload = self.run_cli(case_dir)

        self.assertEqual(payload["proceed"], True)
        self.assertEqual(payload["reason"], "insufficient_meta")
        self.assertIsNone(payload["conceded_ratio"])
        self.assertTrue(payload["warnings"])


if __name__ == "__main__":
    unittest.main()
