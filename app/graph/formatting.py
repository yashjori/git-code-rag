"""Pure formatting helpers for the RAG graph.

Kept free of LLM/vector-store dependencies so build_context and
extract_sources - both explicit unit-test targets - can be tested with
plain RetrievedDocument fixtures.
"""

from __future__ import annotations

from app.retrieval.retriever import RetrievedDocument


def format_context(retrieved_documents: list[RetrievedDocument]) -> str:
    """Render retrieved chunks the way the answer-generation prompt expects.

    SOURCE 1
    File: app/auth/service.py
    Lines: 31-65

    <code>
    """

    sections = []
    for index, item in enumerate(retrieved_documents, start=1):
        metadata = item.document.metadata
        sections.append(
            f"SOURCE {index}\n"
            f"File: {metadata.get('file_path', 'unknown')}\n"
            f"Lines: {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')}\n\n"
            f"{item.document.page_content}"
        )
    return "\n\n".join(sections)


def extract_sources(retrieved_documents: list[RetrievedDocument]) -> list[dict]:
    """Build the unique source list from retrieved metadata.

    Never derived from the LLM's answer text - only from what was actually
    retrieved, so a source can never be fabricated.
    """

    seen: set[tuple] = set()
    sources: list[dict] = []
    for item in retrieved_documents:
        metadata = item.document.metadata
        key = (metadata.get("file_path"), metadata.get("start_line"), metadata.get("end_line"))
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "file_path": metadata.get("file_path"),
                "start_line": metadata.get("start_line"),
                "end_line": metadata.get("end_line"),
            }
        )
    return sources
