"""Lightweight, regex-based symbol detection.

This is intentionally not AST or Tree-sitter based (out of scope for V1 per
spec). It gives each chunk a best-effort symbol_name/symbol_type so search
results are more useful, and is isolated here so it can be swapped for a
real parser later without touching the chunker or pipeline.
"""

from __future__ import annotations

import re

_PATTERNS_BY_LANGUAGE: dict[str, list[tuple[re.Pattern[str], str]]] = {
    "python": [
        (re.compile(r"^\s*class\s+(\w+)"), "class"),
        (re.compile(r"^\s*(?:async\s+)?def\s+(\w+)"), "function"),
    ],
    "javascript": [
        (re.compile(r"^\s*class\s+(\w+)"), "class"),
        (re.compile(r"^\s*(?:export\s+)?(?:default\s+)?function\s*\*?\s+(\w+)"), "function"),
        (
            re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\("),
            "function",
        ),
    ],
    "java": [
        (re.compile(r"^\s*(?:public|private|protected)?\s*(?:static\s+)?class\s+(\w+)"), "class"),
        (re.compile(r"^\s*(?:public|private|protected)?\s*interface\s+(\w+)"), "interface"),
        (
            re.compile(
                r"^\s*(?:public|private|protected)\s+(?:static\s+)?[\w<>\[\],\s]+?\s(\w+)\s*\([^;{}]*\)\s*\{"
            ),
            "method",
        ),
    ],
    "go": [
        (re.compile(r"^\s*type\s+(\w+)\s+struct"), "struct"),
        (re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?(\w+)"), "function"),
    ],
    "rust": [
        (re.compile(r"^\s*(?:pub\s+)?struct\s+(\w+)"), "struct"),
        (re.compile(r"^\s*impl(?:<[^>]*>)?\s+(\w+)"), "impl"),
        (re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)"), "function"),
    ],
}

# javascript patterns are close enough to typescript, c is close enough to cpp
_PATTERNS_BY_LANGUAGE["typescript"] = _PATTERNS_BY_LANGUAGE["javascript"]
_PATTERNS_BY_LANGUAGE["csharp"] = _PATTERNS_BY_LANGUAGE["java"]


def detect_symbol(chunk_text: str, language: str) -> tuple[str | None, str | None]:
    """Return (symbol_name, symbol_type) for the first symbol found in a chunk.

    Returns (None, None) when the language has no pattern set or nothing
    matches - this is an explicitly optional field.
    """

    patterns = _PATTERNS_BY_LANGUAGE.get(language)
    if not patterns:
        return None, None

    for line in chunk_text.splitlines():
        for pattern, symbol_type in patterns:
            match = pattern.match(line)
            if match:
                return match.group(1), symbol_type

    return None, None
