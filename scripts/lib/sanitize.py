"""Prompt-injection sanitiser for orchestrator-ingested text.

Trust boundary policy is declared in CLAUDE.md "신뢰 경계 (Control-Plane Trust Boundary)".
This module is the enforcement helper. Stdlib only.
"""
from __future__ import annotations

import re
from typing import Final

MAX_INPUT_LENGTH: Final[int] = 200_000
_CONTEXT_WINDOW: Final[int] = 40

_PATTERN_STRINGS: tuple[str, ...] = (
    r"\[(?:SYSTEM|ASSISTANT|USER|IGNORE|OVERRIDE|MANUAL_REQUIRED|PRIVILEGED)\]",
    r"\[(?:시스템|사용자|지시|어시스턴트)\]",
    r"\[(?:INTERNAL|EXTERNAL)\]",
    r"<\s*/?\s*(?:system|user|assistant|instruction|instructions|untrusted_content)\s*>",
    r"<\|(?:im_start|im_end|endoftext)\|>",
    r"ignore\s+(?:the\s+)?(?:previous|prior|above|all)\s+(?:instructions?|prompts?)",
    r"disregard\s+(?:the\s+)?(?:previous|prior|above|all)\s+(?:instructions?|prompts?)",
    r"forget\s+(?:everything|all)\s+(?:you\s+)?(?:know|learned|were\s+told)",
    r"new\s+instructions\s*[:\-]",
    r"you\s+are\s+now\b(?:\s+(?:a|an|the))?(?:\s+[a-z][a-z_-]*){0,4}",
    r"system\s+override",
    r"이전\s*지시(?:사항)?(?:을|를)?\s*(?:무시|잊)",
    r"이제부터\s+(?:너는|당신은)",
    r"앞(?:의|에)\s*(?:지시|명령)(?:을|를)?\s*무시",
    r"지금까지의?\s*(?:지시|명령)(?:을|를)?\s*무시",
    r"시스템\s*프롬프트(?:를|을)?\s*(?:출력|보여|알려)",
)
_COMPILED_PATTERNS: Final[tuple[re.Pattern[str], ...]] = tuple(
    re.compile(pattern, re.IGNORECASE) for pattern in _PATTERN_STRINGS
)


def _context_snippet(text: str, start: int, end: int) -> str:
    left = max(0, start - _CONTEXT_WINDOW)
    right = min(len(text), end + _CONTEXT_WINDOW)
    return text[left:right]


def sanitize(text: str | None, *, source: str) -> tuple[str, list[dict[str, object]]]:
    """Escape prompt-injection markers and return (sanitised_text, audit_matches)."""
    if text is None:
        return "", []
    if len(text) > MAX_INPUT_LENGTH:
        raise ValueError(
            f"sanitize(): input length {len(text)} exceeds MAX_INPUT_LENGTH={MAX_INPUT_LENGTH}"
        )

    raw_matches: list[dict[str, object]] = []
    for pattern in _COMPILED_PATTERNS:
        for match in pattern.finditer(text):
            raw_matches.append(
                {
                    "pattern": pattern.pattern,
                    "match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "source": source,
                    "context": _context_snippet(text, match.start(), match.end()),
                }
            )

    if not raw_matches:
        return text, []

    raw_matches.sort(key=lambda item: (int(item["start"]), -(int(item["end"]) - int(item["start"]))))

    filtered_matches: list[dict[str, object]] = []
    for match in raw_matches:
        if not filtered_matches:
            filtered_matches.append(match)
            continue

        previous = filtered_matches[-1]
        if int(match["start"]) < int(previous["end"]):
            continue
        filtered_matches.append(match)

    sanitised = text
    for match in sorted(filtered_matches, key=lambda item: int(item["start"]), reverse=True):
        start = int(match["start"])
        end = int(match["end"])
        original = sanitised[start:end]
        sanitised = f"{sanitised[:start]}<escape>{original}</escape>{sanitised[end:]}"

    return sanitised, filtered_matches


def wrap_as_untrusted(text: str | None, *, source: str, path: str) -> str:
    """Sanitise and wrap a blob with a structural untrusted-content delimiter."""
    sanitised, _ = sanitize(text, source=source)
    return (
        f'<untrusted_content source="{source}" path="{path}">\n'
        f"{sanitised}\n"
        "</untrusted_content>"
    )
