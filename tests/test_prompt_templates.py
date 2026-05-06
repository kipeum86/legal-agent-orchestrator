from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "skills" / "prompt-templates"
ROUTE_CASE = REPO_ROOT / "skills" / "route-case.md"

AGENT_TEMPLATES = {
    "general-legal-research": "general-legal-research.md",
    "PIPA-expert": "pipa-expert.md",
    "GDPR-expert": "gdpr-expert.md",
    "data-protection-agent": "data-protection-agent.md",
    "game-legal-research": "game-legal-research.md",
    "contract-review-agent": "contract-review-agent.md",
    "legal-translation-agent": "legal-translation-agent.md",
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
        self.assertLess(line_count, 430)


if __name__ == "__main__":
    unittest.main()
