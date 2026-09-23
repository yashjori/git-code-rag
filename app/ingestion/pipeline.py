"""Ingestion pipeline: scan -> filter -> load -> chunk -> attach metadata.

Embedding and vector storage are wired in on top of this module's output
(see app/services/repository_service.py) rather than inside it, so this
stage can be exercised and tested without any network calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document

from app.core.config import Settings
from app.core.logging import get_logger
from app.ingestion.chunker import chunk_file_content
from app.ingestion.filters import is_indexable_file
from app.ingestion.language import detect_language
from app.ingestion.loader import load_file_text
from app.ingestion.scanner import discover_files
from app.repositories.identity import RepositoryReference

logger = get_logger(__name__)


@dataclass(frozen=True)
class ChunkingStats:
    files_scanned: int
    files_indexed: int
    chunks_created: int


def _build_document(
    raw_chunk, *, reference: RepositoryReference, relative_path: str, file_name: str, language: str
) -> Document:
    return Document(
        page_content=raw_chunk.content,
        metadata={
            "repository_id": reference.repository_id,
            "provider": reference.provider,
            "branch": reference.branch,
            "file_path": relative_path,
            "file_name": file_name,
            "language": language,
            "chunk_index": raw_chunk.chunk_index,
            "start_line": raw_chunk.start_line,
            "end_line": raw_chunk.end_line,
            "symbol_name": raw_chunk.symbol_name,
            "symbol_type": raw_chunk.symbol_type,
        },
    )


def build_documents_for_repository(
    local_path: Path,
    reference: RepositoryReference,
    settings: Settings,
) -> tuple[list[Document], ChunkingStats]:
    """Turn a checked-out repository into LangChain Documents.

    Each Document's page_content is one code chunk; its metadata carries
    everything needed for Qdrant payload filtering and source citations.
    """

    local_path = local_path.resolve()
    documents: list[Document] = []
    files_scanned = 0
    files_indexed = 0

    for file_path in discover_files(local_path):
        files_scanned += 1

        if not is_indexable_file(file_path, settings.max_index_file_size_kb):
            continue

        content = load_file_text(file_path)
        if content is None:
            continue

        language = detect_language(file_path)
        raw_chunks = chunk_file_content(
            content, language, settings.chunk_size, settings.chunk_overlap
        )
        if not raw_chunks:
            continue

        relative_path = file_path.relative_to(local_path).as_posix()
        documents.extend(
            _build_document(
                raw_chunk,
                reference=reference,
                relative_path=relative_path,
                file_name=file_path.name,
                language=language,
            )
            for raw_chunk in raw_chunks
        )
        files_indexed += 1

    stats = ChunkingStats(
        files_scanned=files_scanned,
        files_indexed=files_indexed,
        chunks_created=len(documents),
    )
    logger.info(
        "chunking completed: files_scanned=%d files_indexed=%d chunks_created=%d",
        stats.files_scanned,
        stats.files_indexed,
        stats.chunks_created,
    )
    return documents, stats
