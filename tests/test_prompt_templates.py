from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "skills" / "prompt-templates"
ROUTE_CASE = REPO_ROOT / "skills" / "route-case.md"
MANAGE_DEBATE = REPO_ROOT / "skills" / "manage-debate.md"
CLAUDE = REPO_ROOT / "CLAUDE.md"

AGENT_TEMPLATES = {
    "legal-research-agent": "legal-research-agent.md",
    "data-protection-agent": "data-protection-agent.md",
    "legal-writing-agent": "legal-writing-agent.md",
    "second-review-agent": "second-review-agent.md",
}

COMMON_PLACEHOLDERS = {
    "{{STYLE_GUIDE_BLOCK}}",
    "{{ERROR_CONTRACT_BLOCK}}",
    "{{OUTPUT_CONTRACT_BLOCK}}",
}


class PromptTemplateTests(unittest.TestCase):
    def test_route_case_references_all_agent_templates(self) -> None:
        text = ROUTE_CASE.read_text(encoding="utf-8")
        for filename in AGENT_TEMPLATES.values():
            with self.subTest(filename=filename):
                self.assertIn(f"skills/prompt-templates/{filename}", text)

    def test_agent_templates_exist_and_declare_agent_id(self) -> None:
        for agent_id, filename in AGENT_TEMPLATES.items():
            with self.subTest(agent_id=agent_id):
                path = TEMPLATE_DIR / filename
                self.assertTrue(path.exists(), path)
                text = path.read_text(encoding="utf-8")
                self.assertIn(f'# AGENT_ID = "{agent_id}"', text)

    def test_common_blocks_define_all_placeholders(self) -> None:
        text = (TEMPLATE_DIR / "common-blocks.md").read_text(encoding="utf-8")
        for placeholder in COMMON_PLACEHOLDERS:
            with self.subTest(placeholder=placeholder):
                self.assertIn(placeholder, text)

    def test_template_placeholders_are_known(self) -> None:
        known = COMMON_PLACEHOLDERS | {
            "{질문}",
            "{PROJECT_ROOT}",
            "{OUTPUT_DIR}",
            "{AGENT_ID}",
            "{CASE_ID}",
            "{CONTRACT_PATH}",
            "{SOURCE_TEXT_OR_PATH}",
            "{SOURCE_LANG}",
            "{TARGET_LANG}",
            "{SUMMARY}",
            "{KEY_FINDINGS}",
            "{AGENT_A_ID}",
            "{AGENT_B_ID}",
            "{SUMMARY_A}",
            "{SUMMARY_B}",
            "{KEY_FINDINGS_A}",
            "{KEY_FINDINGS_B}",
            "{failure_reason}",
            "{agent_id}",
            "{관할권/도메인}",
            "{사유}",
            "{RESEARCH_SUMMARY}",
            "{스페셜리스트명_A}",
            "{스페셜리스트명_B}",
            "{RESEARCH_MODE}",
            "{ROUTE_MODE}",
            "{CO_RUNNING_AGENTS}",
        }
        pattern = re.compile(r"(\{\{[A-Z_]+\}\}|\{[^{}\n]+\})")
        for path in sorted(TEMPLATE_DIR.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for placeholder in pattern.findall(text):
                if placeholder.startswith('{"') or placeholder.startswith('{ "'):
                    continue
                with self.subTest(path=path.name, placeholder=placeholder):
                    self.assertIn(placeholder, known)

    def test_route_case_is_no_longer_prompt_template_monolith(self) -> None:
        line_count = len(ROUTE_CASE.read_text(encoding="utf-8").splitlines())
        self.assertLess(line_count, 500)

    def test_intake_query_is_passed_as_argv_not_environment(self) -> None:
        text = CLAUDE.read_text(encoding="utf-8")
        self.assertIn("CLIENT_QUERY", text)
        self.assertIn('sys.argv[2][:200]', text)
        self.assertNotIn("USER_QUERY", text)

    def test_route_case_persists_classification_and_writes_route_atomically(self) -> None:
        text = ROUTE_CASE.read_text(encoding="utf-8")
        self.assertIn('$OUTPUT_DIR/classification.json', text)
        self.assertIn('cat > "$OUTPUT_DIR/classification.json"', text)
        self.assertIn('mktemp "$OUTPUT_DIR/route-selection.XXXXXX.json"', text)
        self.assertIn('mv "$ROUTE_TMP" "$OUTPUT_DIR/route-selection.json"', text)

    def test_manage_debate_uses_active_roster_and_required_meta_fields(self) -> None:
        text = MANAGE_DEBATE.read_text(encoding="utf-8")
        self.assertNotIn("8-agent roster", text)
        self.assertIn("active 4-agent roster", text)

        round3_meta = re.search(
            r"\{OUTPUT_DIR\}/debate-round-3-\{AGENT_A_ID\}-meta\.json:\n(?P<body>\{.*?\n\})",
            text,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(round3_meta)
        self.assertIn('"key_findings"', round3_meta.group("body"))

        writing_meta = re.search(
            r"\{OUTPUT_DIR\}/writing-meta\.json\n\s+(?P<body>\{.*?\})",
            text,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(writing_meta)
        self.assertIn('"key_findings"', writing_meta.group("body"))

    def test_review_completion_is_bound_before_delivery_for_patterns_1_and_2(self) -> None:
        route_text = ROUTE_CASE.read_text(encoding="utf-8")
        pattern1_review = route_text.index("10. **second-review-agent review.")
        partial_failure = route_text.index("### Partial failure handling", pattern1_review)
        self.assertIn("bind-review.py", route_text[pattern1_review:partial_failure])
        self.assertIn("소급", route_text[pattern1_review:partial_failure])

        claude_text = CLAUDE.read_text(encoding="utf-8")
        step4 = claude_text.index("### Step 4: Hand-off")
        step5 = claude_text.index("### Step 5: Final Delivery", step4)
        self.assertIn("second-review-agent", claude_text[step4:step5])
        self.assertIn("bind-review.py", claude_text[step4:step5])

    def test_docx_loop_stops_before_logging_when_conversion_fails(self) -> None:
        text = (REPO_ROOT / "skills" / "deliver-output.md").read_text(encoding="utf-8")
        step7 = text.index("## Step 7: Generate DOCX deliverables")
        step8 = text.index("## Step 8: Finalize events.jsonl", step7)
        block = text[step7:step8]
        conversion = 'if ! python3 "$PROJECT_ROOT/scripts/md-to-docx.py"'
        self.assertIn(conversion, block)
        self.assertIn("exit 3", block)
        conversion_pos = block.index(conversion)
        log_pos = block.index("--type docx_generated")
        self.assertLess(conversion_pos, block.index("exit 3", conversion_pos))
        self.assertLess(block.index("  fi", conversion_pos), log_pos)

    def test_mcp_fallback_verification_contract_requires_passed(self) -> None:
        debate_text = MANAGE_DEBATE.read_text(encoding="utf-8")
        fallback = debate_text.index("MCP fallback verification event:")
        disclosure = debate_text.index("Disclosure to inject", fallback)
        self.assertIn('"passed":true', debate_text[fallback:disclosure])
        self.assertIn("`passed: false`", debate_text[fallback:disclosure])

        route_text = ROUTE_CASE.read_text(encoding="utf-8")
        row = next(line for line in route_text.splitlines() if "`mcp_fallback_verification`" in line)
        self.assertIn("`passed`", row)

    def test_citation_verification_contract_scopes_source_ids_by_agent(self) -> None:
        schema = (REPO_ROOT / "schemas" / "review-meta.schema.json").read_text(encoding="utf-8")
        self.assertIn('"agent_id"', schema)

        second_review = (TEMPLATE_DIR / "second-review-agent.md").read_text(encoding="utf-8")
        self.assertIn('"agent_id": "legal-research-agent"', second_review)
        self.assertIn("agent_id를 반드시", second_review)
        self.assertIn("원본 meta에 source_id가 있으면", second_review)

        debate = MANAGE_DEBATE.read_text(encoding="utf-8")
        self.assertIn('"agent_id": "AGENT_ID"', debate)
        self.assertIn("agent_id를 반드시", debate)
        self.assertIn("원본 meta에 source_id가 있으면", debate)


if __name__ == "__main__":
    unittest.main()
