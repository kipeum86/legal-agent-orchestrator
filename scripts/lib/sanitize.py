"""Prompt-injection sanitiser for orchestrator-ingested text.

Trust boundary policy is declared in CLAUDE.md "Trust Boundary (Control-Plane)".
This module is the enforcement helper. Stdlib only.
"""
from __future__ import annotations

import re
import unicodedata
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
_ESCAPE_BLOCK_RE: Final[re.Pattern[str]] = re.compile(r"<escape>.*?</escape>", re.DOTALL)
_LITERAL_ESCAPE_TAG_RE: Final[re.Pattern[str]] = re.compile(r"</?escape>", re.IGNORECASE)
_ZERO_WIDTH_OR_CONTROL_RE: Final[re.Pattern[str]] = re.compile(
    r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]"
)
_EMAIL_RE: Final[re.Pattern[str]] = re.compile(
    r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)
_RRN_DASHED_RE: Final[re.Pattern[str]] = re.compile(r"(?<!\d)\d{6}-\d{7}(?!\d)")
_RRN_COMPACT_RE: Final[re.Pattern[str]] = re.compile(r"(?<!\d)\d{13}(?!\d)")
_PHONE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?<!\d)(?:\+82[-.\s]?)?0(?:2|1[016789]|[3-6]\d)[-.\s]?\d{3,4}[-.\s]?\d{4}(?!\d)"
)
_CARD_CANDIDATE_RE: Final[re.Pattern[str]] = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
_SECRET_PATTERNS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    ("api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")),
    ("github_token", re.compile(r"\bghp_[A-Za-z0-9_]{20,}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")),
)
_EXTERNAL_IMAGE_RE: Final[re.Pattern[str]] = re.compile(
    r"!\[[^\]\n]*\]\((?:https?:)?//[^)\s]+[^)]*\)",
    re.IGNORECASE,
)


def _context_snippet(text: str, start: int, end: int) -> str:
    left = max(0, start - _CONTEXT_WINDOW)
    right = min(len(text), end + _CONTEXT_WINDOW)
    return text[left:right]


def _neutralize_literal_escape_tags(text: str) -> str:
    return _LITERAL_ESCAPE_TAG_RE.sub(lambda match: match.group(0).replace("<", "&lt;").replace(">", "&gt;"), text)


def _normalize_untrusted_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    return _ZERO_WIDTH_OR_CONTROL_RE.sub("", normalized)


def _luhn_valid(digits: str) -> bool:
    checksum = 0
    parity = len(digits) % 2
    for index, char in enumerate(digits):
        value = ord(char) - ord("0")
        if index % 2 == parity:
            value *= 2
            if value > 9:
                value -= 9
        checksum += value
    return checksum % 10 == 0


def _redact_sensitive(text: str) -> str:
    spans: list[tuple[int, int, str]] = []

    def add_span(start: int, end: int, kind: str) -> None:
        if any(start < existing_end and end > existing_start for existing_start, existing_end, _ in spans):
            return
        spans.append((start, end, kind))

    for pattern, kind in (
        (_RRN_DASHED_RE, "rrn"),
        (_RRN_COMPACT_RE, "rrn"),
        (_EMAIL_RE, "email"),
        (_PHONE_RE, "phone"),
        (_EXTERNAL_IMAGE_RE, "external_image"),
    ):
        for match in pattern.finditer(text):
            add_span(match.start(), match.end(), kind)

    for kind, pattern in _SECRET_PATTERNS:
        for match in pattern.finditer(text):
            add_span(match.start(), match.end(), kind)

    for match in _CARD_CANDIDATE_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits) <= 19 and _luhn_valid(digits):
            add_span(match.start(), match.end(), "card")

    if not spans:
        return text

    spans.sort(key=lambda item: item[0])
    parts: list[str] = []
    cursor = 0
    for start, end, kind in spans:
        parts.append(text[cursor:start])
        parts.append(f"[REDACTED:{kind}]")
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts)


def _escape_inner_ranges(text: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for match in _ESCAPE_BLOCK_RE.finditer(text):
        inner_start = match.start() + len("<escape>")
        inner_end = match.end() - len("</escape>")
        ranges.append((inner_start, inner_end))
    return ranges


def _is_inside_range(start: int, end: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start >= range_start and end <= range_end for range_start, range_end in ranges)


def sanitize(
    text: str | None,
    *,
    source: str,
    redact: bool = True,
) -> tuple[str, list[dict[str, object]]]:
    """Escape prompt-injection markers and return (sanitised_text, audit_matches)."""
    if text is None:
        return "", []
    if len(text) > MAX_INPUT_LENGTH:
        raise ValueError(
            f"sanitize(): input length {len(text)} exceeds MAX_INPUT_LENGTH={MAX_INPUT_LENGTH}"
        )

    text = _normalize_untrusted_text(_neutralize_literal_escape_tags(text))
    if redact:
        text = _redact_sensitive(text)

    escape_ranges = _escape_inner_ranges(text)
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
                    "escaped": _is_inside_range(match.start(), match.end(), escape_ranges),
                }
            )

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

    unescaped_matches = [match for match in filtered_matches if not bool(match["escaped"])]
    if not unescaped_matches:
        return text, filtered_matches

    parts: list[str] = []
    cursor = 0
    for match in unescaped_matches:
        start = int(match["start"])
        end = int(match["end"])
        parts.append(text[cursor:start])
        parts.append("<escape>")
        parts.append(text[start:end])
        parts.append("</escape>")
        cursor = end
    parts.append(text[cursor:])

    return "".join(parts), filtered_matches


def wrap_as_untrusted(text: str | None, *, source: str, path: str) -> str:
    """Sanitise and wrap a blob with a structural untrusted-content delimiter."""
    sanitised, _ = sanitize(text, source=source)
    return (
        f'<untrusted_content source="{source}" path="{path}">\n'
        f"{sanitised}\n"
        "</untrusted_content>"
    )
