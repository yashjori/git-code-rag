"""Semantic retrieval, scoped to one repository and branch.

Wraps QdrantVectorStoreService so the rest of the app (LangGraph nodes)
works with LangChain Documents rather than raw Qdrant search results.
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.documents import Document

from app.core.logging import get_logger
from app.vectorstore.qdrant_store import QdrantVectorStoreService

logger = get_logger(__name__)


@dataclass(frozen=True)
class RetrievedDocument:
    document: Document
    score: float


class CodeRetriever:
    def __init__(self, vector_store: QdrantVectorStoreService, top_k: int) -> None:
        self._vector_store = vector_store
        self._top_k = top_k

    def retrieve(
        self, query: str, *, repository_id: str, branch: str
    ) -> list[RetrievedDocument]:
        logger.info(
            "retrieval query: repository_id=%s branch=%s top_k=%d",
            repository_id,
            branch,
            self._top_k,
        )
        results = self._vector_store.similarity_search(
            query, repository_id=repository_id, branch=branch, top_k=self._top_k
        )
        logger.info("retrieved document count: %d", len(results))

        return [
            RetrievedDocument(
                document=Document(page_content=result.content, metadata=result.metadata),
                score=result.score,
            )
            for result in results
        ]
