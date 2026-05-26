#!/usr/bin/env python3
"""Check engineering audit remediation acceptance criteria."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_STYLE_GUIDE = "legal-writing-formatting-guide.md"


@dataclass(frozen=True)
class CheckResult:
    id: int
    title: str
    passed: bool
    evidence: list[str]


def read_text(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def exists(path: str) -> bool:
    return (REPO_ROOT / path).exists()


def git_tracked(path: str) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def has(path: str, needle: str) -> bool:
    return needle in read_text(path)


def regex_has(path: str, pattern: str) -> bool:
    return re.search(pattern, read_text(path), re.MULTILINE) is not None


def exact_mcp_pins() -> bool:
    payload = json.loads(read_text(".mcp.json"))
    servers = payload.get("mcpServers", {})
    specs = {
        name: next((arg for arg in server.get("args", []) if isinstance(arg, str) and not arg.startswith("-")), "")
        for name, server in servers.items()
    }
    return (
        specs.get("korean-law") == "korean-law-mcp@3.5.4"
        and specs.get("kordoc") == "kordoc@2.5.2"
        and all("@latest" not in spec for spec in specs.values())
    )


def result(id_: int, title: str, conditions: list[tuple[bool, str]]) -> CheckResult:
    return CheckResult(
        id=id_,
        title=title,
        passed=all(condition for condition, _ in conditions),
        evidence=[f"{'PASS' if condition else 'FAIL'}: {message}" for condition, message in conditions],
    )


def check_style_guide() -> CheckResult:
    return result(
        1,
        "fresh clone에서 canonical style guide 경로가 존재한다",
        [
            (exists(CANONICAL_STYLE_GUIDE), f"{CANONICAL_STYLE_GUIDE} exists"),
            (git_tracked(CANONICAL_STYLE_GUIDE), "canonical style guide is tracked by git"),
            (has("skills/prompt-templates/common-blocks.md", CANONICAL_STYLE_GUIDE), "prompt common block references canonical guide"),
        ],
    )


def check_output_dir_contract() -> CheckResult:
    return result(
        2,
        "LEGAL_ORCHESTRATOR_PRIVATE_DIR와 무관하게 단일 OUTPUT_DIR 계약을 사용한다",
        [
            (has("CLAUDE.md", 'OUTPUT_DIR="$PRIVATE_DIR/$CASE_ID"'), "CLAUDE.md defines OUTPUT_DIR from PRIVATE_DIR and CASE_ID"),
            (has("CLAUDE.md", "LEGAL_ORCHESTRATOR_PRIVATE_DIR"), "CLAUDE.md documents private dir override"),
            (has("skills/deliver-output.md", "$OUTPUT_DIR"), "deliver-output uses OUTPUT_DIR as work-product directory"),
            (has("skills/prompt-templates/common-blocks.md", "{OUTPUT_DIR}/{AGENT_ID}-result.md"), "agent output template uses OUTPUT_DIR placeholder"),
        ],
    )


def check_event_writer() -> CheckResult:
    return result(
        3,
        "모든 이벤트는 JSON writer를 통해 기록된다",
        [
            (exists("scripts/log-event.py"), "scripts/log-event.py exists"),
            (has("scripts/log-event.py", "fcntl.flock"), "log-event.py uses file locking"),
            (exists("tests/test_log_event.py"), "log-event regression tests exist"),
            (has("CLAUDE.md", "scripts/log-event.py"), "orchestrator prompt references log-event.py"),
        ],
    )


def check_validation() -> CheckResult:
    return result(
        4,
        "validate-case.py가 이벤트와 meta schema를 검증한다",
        [
            (exists("schemas/events.schema.json"), "events schema exists"),
            (exists("schemas/agent-meta.schema.json"), "agent meta schema exists"),
            (exists("schemas/review-meta.schema.json"), "review meta schema exists"),
            (exists("scripts/validate-case.py"), "validate-case.py exists"),
            (has("tests/test_validate_case.py", "--mode"), "warn/strict mode tests exist"),
            (has("tests/test_validate_case.py", "missing citation"), "source_graded citation validation is tested"),
        ],
    )


def check_sources_merge() -> CheckResult:
    return result(
        5,
        "sources.json은 deterministic script로 생성된다",
        [
            (exists("scripts/merge-sources.py"), "merge-sources.py exists"),
            (has("skills/deliver-output.md", "scripts/merge-sources.py"), "deliver-output invokes merge-sources.py"),
            (has("scripts/merge-sources.py", "normalize_key"), "merge-sources.py normalizes title/citation keys"),
            (exists("tests/test_merge_sources.py"), "merge-sources tests exist"),
        ],
    )


def check_case_report_meta() -> CheckResult:
    return result(
        6,
        "case-report.md는 모든 *-meta.json을 반영한다",
        [
            (exists("scripts/generate-case-report.py"), "generate-case-report.py exists"),
            (has("scripts/generate-case-report.py", 'glob("*-meta.json")'), "case-report generator discovers *-meta.json"),
            (exists("tests/fixtures/cases/pattern1-multi-agent/data-protection-agent-meta.json"), "data-protection-agent meta fixture exists"),
            (exists("tests/fixtures/cases/pattern1-multi-agent/legal-research-agent-meta.json"), "legal-research-agent meta fixture exists"),
            (has("tests/test_generate_case_report.py", "데이터보호 스페셜리스트"), "case-report test asserts data-protection specialist appears"),
            (has("tests/test_generate_case_report.py", "법률 리서치 스페셜리스트"), "case-report test asserts legal-research specialist appears"),
        ],
    )


def check_finalization_gate() -> CheckResult:
    return result(
        7,
        "review 미승인 상태에서는 최종 승인 산출물처럼 기록되지 않는다",
        [
            (exists("scripts/finalize-case.py"), "finalize-case.py exists"),
            (has("skills/deliver-output.md", "finalize-case.py"), "deliver-output gates finalization through finalize-case.py"),
            (has("tests/test_finalize_case.py", "revision_needed_blocks_final_output"), "revision_needed block is tested"),
            (has("tests/test_finalize_case.py", "pipeline_aborted"), "pipeline_aborted event is tested"),
        ],
    )


def check_debate_transcript() -> CheckResult:
    return result(
        8,
        "Pattern 3 transcript는 deterministic concat으로 생성된다",
        [
            (exists("scripts/build-debate-transcript.py"), "build-debate-transcript.py exists"),
            (has("skills/manage-debate.md", "build-debate-transcript.py"), "manage-debate invokes transcript builder"),
            (has("skills/manage-debate.md", "transcript generation step must not use an LLM"), "manage-debate forbids LLM transcript generation"),
            (exists("tests/test_build_debate_transcript.py"), "debate transcript tests exist"),
        ],
    )


def check_round3_decision() -> CheckResult:
    return result(
        9,
        "Pattern 3 Round 3 진행 여부는 동일 meta에 대해 재현 가능하게 결정된다",
        [
            (exists("scripts/decide-debate-round3.py"), "decide-debate-round3.py exists"),
            (has("skills/manage-debate.md", "decide-debate-round3.py"), "manage-debate invokes Round 3 decision script"),
            (has("tests/test_decide_debate_round3.py", "first = self.run_cli"), "determinism test executes the same case twice"),
            (has("tests/test_decide_debate_round3.py", "insufficient_meta"), "malformed meta fallback is tested"),
        ],
    )


def check_docx_injection_residue() -> CheckResult:
    return result(
        10,
        "최종 DOCX에는 unescaped prompt-injection marker가 남지 않는다",
        [
            (has("scripts/sanitize-check.py", "--fail-on-unescaped"), "sanitize-check exposes --fail-on-unescaped"),
            (has("skills/deliver-output.md", "--fail-on-unescaped"), "deliver-output uses --fail-on-unescaped"),
            (has("scripts/md-to-docx.py", "ESCAPED_OMISSION_TEXT"), "md-to-docx omits escaped instruction-like text by default"),
            (has("tests/test_md_to_docx_escape_policy.py", "assertNotIn(\"[SYSTEM]\""), "DOCX omission policy is tested"),
        ],
    )


def check_dependency_pinning() -> CheckResult:
    return result(
        11,
        "하위 에이전트는 setup.sh로 재현 가능하게 설치되고, MCP dependency는 정확한 버전으로 pin된다",
        [
            (exists("setup.sh"), "setup.sh exists"),
            (has("setup.sh", "--depth 1"), "setup.sh uses shallow clone (--depth 1)"),
            (has("setup.sh", "legal-research-agent") and has("setup.sh", "data-protection-agent"), "setup.sh enumerates all 4 subordinate agents"),
            (exact_mcp_pins(), ".mcp.json pins exact MCP package versions"),
            (exists("tests/test_mcp_pins.py"), "MCP pin tests exist"),
        ],
    )


def check_mcp_monitoring() -> CheckResult:
    return result(
        12,
        "MCP pinning에는 업데이트 알림 경로가 있다",
        [
            (exists(".github/workflows/mcp-version-monitor.yml"), "MCP version monitor workflow exists"),
            (has(".github/workflows/mcp-version-monitor.yml", "schedule:"), "workflow runs on schedule"),
            (has(".github/workflows/mcp-version-monitor.yml", "issues: write"), "workflow can open/update issues"),
            (exists("MCP_VERSION_CHANGELOG.md"), "MCP version changelog exists"),
            (has("MCP_VERSION_CHANGELOG.md", "korean-law-mcp"), "changelog records korean-law-mcp pin"),
            (has("MCP_VERSION_CHANGELOG.md", "kordoc"), "changelog records kordoc pin"),
        ],
    )


CHECKS: tuple[Callable[[], CheckResult], ...] = (
    check_style_guide,
    check_output_dir_contract,
    check_event_writer,
    check_validation,
    check_sources_merge,
    check_case_report_meta,
    check_finalization_gate,
    check_debate_transcript,
    check_round3_decision,
    check_docx_injection_residue,
    check_dependency_pinning,
    check_mcp_monitoring,
)


def run_checks() -> list[CheckResult]:
    return [check() for check in CHECKS]


def to_json(results: list[CheckResult]) -> str:
    return json.dumps(
        {
            "passed": all(item.passed for item in results),
            "total": len(results),
            "passed_count": sum(1 for item in results if item.passed),
            "checks": [
                {
                    "id": item.id,
                    "title": item.title,
                    "passed": item.passed,
                    "evidence": item.evidence,
                }
                for item in results
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


def to_markdown(results: list[CheckResult]) -> str:
    passed_count = sum(1 for item in results if item.passed)
    lines = [
        "# Engineering Audit Acceptance Report",
        "",
        f"Status: {'PASS' if passed_count == len(results) else 'FAIL'} ({passed_count}/{len(results)} criteria)",
        "",
        "| # | Criterion | Status |",
        "|---:|---|---|",
    ]
    for item in results:
        lines.append(f"| {item.id} | {item.title} | {'PASS' if item.passed else 'FAIL'} |")
    lines.append("")
    for item in results:
        lines.append(f"## {item.id}. {item.title}")
        lines.append("")
        lines.extend(f"- {line}" for line in item.evidence)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check audit remediation acceptance criteria.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument("--write", type=Path, default=None, help="Write Markdown report to this path.")
    args = parser.parse_args(argv)

    results = run_checks()
    output = to_json(results) if args.json else to_markdown(results)
    if args.write is not None:
        args.write.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0 if all(item.passed for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
