from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.lib import review_gate  # noqa: E402


def load_validate_case_module() -> ModuleType:
    module_path = REPO_ROOT / "scripts" / "validate-case.py"
    spec = importlib.util.spec_from_file_location("validate_case", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_schema(name: str) -> dict:
    return json.loads((REPO_ROOT / "schemas" / name).read_text(encoding="utf-8"))


class SchemaDriftTests(unittest.TestCase):
    def test_review_approvals_match_schema(self) -> None:
        module = load_validate_case_module()
        schema = load_schema("review-meta.schema.json")
        self.assertEqual(set(schema["properties"]["approval"]["enum"]), module.REVIEW_APPROVALS)
        self.assertEqual(set(schema["properties"]["approval"]["enum"]),
                         review_gate.VALID_STATUSES)

    def test_citation_statuses_match_schema(self) -> None:
        module = load_validate_case_module()
        schema = load_schema("review-meta.schema.json")
        enum = set(
            schema["properties"]["citation_verification"]["items"]["properties"]["status"]["enum"]
        )
        self.assertEqual(enum, module.CITATION_STATUSES)
        self.assertEqual(enum, review_gate.CITATION_STATUSES)

    def test_source_grades_match_schema(self) -> None:
        module = load_validate_case_module()
        schema = load_schema("agent-meta.schema.json")
        enum = set(schema["properties"]["sources"]["items"]["properties"]["grade"]["enum"])
        self.assertEqual(enum, module.GRADES)


if __name__ == "__main__":
    unittest.main()
