"""File filtering: decide which discovered files are worth indexing."""

from __future__ import annotations

from pathlib import Path

from app.core.config import (
    ALWAYS_INDEX_FILENAMES,
    IGNORED_FILE_SUFFIXES,
    SUPPORTED_FILE_EXTENSIONS,
)

# Suffixes that end in more than one dot-segment (e.g. "*.min.js") can't be
# matched by Path.suffix, which only ever returns the last segment.
_COMPOUND_IGNORED_SUFFIXES = tuple(s for s in IGNORED_FILE_SUFFIXES if s.count(".") > 1)

# Sniff the first chunk of a file for a NUL byte as a cheap, reliable
# binary-file heuristic. Text source files never contain NUL bytes.
_BINARY_SNIFF_BYTES = 8192


def _is_extension_supported(path: Path) -> bool:
    if path.name in ALWAYS_INDEX_FILENAMES:
        return True
    if path.name.endswith(_COMPOUND_IGNORED_SUFFIXES):
        return False
    return path.suffix.lower() in SUPPORTED_FILE_EXTENSIONS


def _is_ignored_suffix(path: Path) -> bool:
    if path.name.endswith(_COMPOUND_IGNORED_SUFFIXES):
        return True
    return path.suffix.lower() in IGNORED_FILE_SUFFIXES


def _looks_like_binary(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            chunk = fh.read(_BINARY_SNIFF_BYTES)
    except OSError:
        return True
    return b"\x00" in chunk


def is_indexable_file(path: Path, max_file_size_kb: int) -> bool:
    """Return True if this file should be scanned, chunked, and indexed."""

    if not path.is_file():
        return False
    if _is_ignored_suffix(path):
        return False
    if not _is_extension_supported(path):
        return False

    try:
        size_kb = path.stat().st_size / 1024
    except OSError:
        return False
    if size_kb > max_file_size_kb:
        return False

    if _looks_like_binary(path):
        return False

    return True
