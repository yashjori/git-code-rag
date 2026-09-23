"""Code-aware chunking.

Phase 1 strategy per spec: use langchain_text_splitters' language-aware
separators (which keep functions/classes/methods together where the
language grammar allows it) and fall back to the generic
RecursiveCharacterTextSplitter for languages/files it doesn't know.

Isolated behind chunk_file_content() so it can be swapped for a
Tree-sitter/AST/symbol-level chunker later without touching the scanner,
filters, loader, or pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.ingestion.language import SPLITTER_LANGUAGE_BY_LANGUAGE
from app.ingestion.symbols import detect_symbol


@dataclass(frozen=True)
class RawChunk:
    """A single chunk of one file's content, before repository-level
    metadata (repository_id, provider, branch, file_path) is attached."""

    content: str
    chunk_index: int
    start_line: int
    end_line: int
    symbol_name: str | None
    symbol_type: str | None


def _build_splitter(language: str, chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    splitter_language = SPLITTER_LANGUAGE_BY_LANGUAGE.get(language)
    if splitter_language is not None:
        return RecursiveCharacterTextSplitter.from_language(
            language=splitter_language,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    return RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def _line_number(content: str, char_index: int) -> int:
    return content.count("\n", 0, char_index) + 1


def chunk_file_content(
    content: str, language: str, chunk_size: int, chunk_overlap: int
) -> list[RawChunk]:
    """Split one file's text into RawChunks with line ranges and best-effort
    symbol detection."""

    if not content.strip():
        return []

    splitter = _build_splitter(language, chunk_size, chunk_overlap)
    pieces = splitter.split_text(content)

    chunks: list[RawChunk] = []
    search_cursor = 0
    for index, piece in enumerate(pieces):
        start_index = content.find(piece, search_cursor)
        if start_index == -1:
            start_index = content.find(piece)
        if start_index == -1:
            start_index = search_cursor

        end_index = start_index + len(piece)
        search_cursor = start_index

        symbol_name, symbol_type = detect_symbol(piece, language)

        chunks.append(
            RawChunk(
                content=piece,
                chunk_index=index,
                start_line=_line_number(content, start_index),
                end_line=_line_number(content, max(end_index - 1, start_index)),
                symbol_name=symbol_name,
                symbol_type=symbol_type,
            )
        )

    return chunks
