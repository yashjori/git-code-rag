"""Language detection from file path.

Kept separate from chunking so it can be unit tested on its own and reused
wherever a human-readable language label is needed for metadata.
"""

from __future__ import annotations

from pathlib import Path

from langchain_text_splitters import Language

_LANGUAGE_BY_EXTENSION: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".sql": "sql",
    ".md": "markdown",
    ".txt": "text",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".toml": "toml",
}

_LANGUAGE_BY_FILENAME: dict[str, str] = {
    "Dockerfile": "dockerfile",
    "docker-compose.yml": "yaml",
    "requirements.txt": "text",
    "pyproject.toml": "toml",
    "package.json": "json",
}

# Only languages langchain_text_splitters knows how to split structurally.
# Everything else falls back to the generic recursive character splitter.
SPLITTER_LANGUAGE_BY_LANGUAGE: dict[str, Language] = {
    "python": Language.PYTHON,
    "javascript": Language.JS,
    "typescript": Language.TS,
    "java": Language.JAVA,
    "csharp": Language.CSHARP,
    "go": Language.GO,
    "rust": Language.RUST,
    "cpp": Language.CPP,
    "c": Language.C,
    "markdown": Language.MARKDOWN,
}


def detect_language(path: Path) -> str:
    """Return a human-readable language label for a file path."""

    if path.name in _LANGUAGE_BY_FILENAME:
        return _LANGUAGE_BY_FILENAME[path.name]
    return _LANGUAGE_BY_EXTENSION.get(path.suffix.lower(), "text")
