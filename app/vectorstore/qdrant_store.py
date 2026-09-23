"""Qdrant Cloud vector store service.

Every other layer (ingestion pipeline, retriever, LangGraph nodes) talks to
this service instead of the raw qdrant_client, so Qdrant-specific details -
collection setup, payload shape, point IDs, filter construction - live in
one place. Repository/branch isolation is enforced here at query time via
payload filters, never left to callers to remember.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from langchain_core.documents import Document
from qdrant_client import QdrantClient, models

from app.core.logging import get_logger
from app.embeddings.service import EmbeddingService

logger = get_logger(__name__)

# Chunk text is stored in payload under this key so it can be returned
# alongside metadata on search - Qdrant does not return the original input
# used for cloud inference automatically.
_CONTENT_PAYLOAD_KEY = "page_content"

_FILTERABLE_PAYLOAD_FIELDS = ("repository_id", "branch")

_UPSERT_BATCH_SIZE = 32


@dataclass(frozen=True)
class SearchResult:
    content: str
    metadata: dict
    score: float


class QdrantVectorStoreService:
    def __init__(
        self,
        *,
        url: str,
        api_key: str,
        collection_name: str,
        embedding_service: EmbeddingService,
    ) -> None:
        self._client = QdrantClient(url=url, api_key=api_key, cloud_inference=True)
        self._collection_name = collection_name
        self._embeddings = embedding_service

    def ensure_collection(self, vector_size: int) -> None:
        """Create the collection if it doesn't exist yet.

        Vector size must match the configured Qdrant Cloud Inference model's
        output dimensionality (QDRANT_EMBEDDING_DIMENSION) - Qdrant will
        reject upserts with a mismatched vector size otherwise.
        """

        if self._client.collection_exists(self._collection_name):
            return

        self._client.create_collection(
            collection_name=self._collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )
        for field_name in _FILTERABLE_PAYLOAD_FIELDS:
            self._client.create_payload_index(
                collection_name=self._collection_name,
                field_name=field_name,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
        logger.info("created Qdrant collection '%s' (size=%d)", self._collection_name, vector_size)

    @staticmethod
    def _point_id(metadata: dict) -> str:
        key = "{repository_id}:{branch}:{file_path}:{chunk_index}".format(**metadata)
        return str(uuid.uuid5(uuid.NAMESPACE_URL, key))

    def add_documents(self, documents: list[Document]) -> int:
        """Embed and upsert chunks. Returns the number of points written."""

        points = [
            models.PointStruct(
                id=self._point_id(document.metadata),
                vector=self._embeddings.to_inference_document(document.page_content),
                payload={_CONTENT_PAYLOAD_KEY: document.page_content, **document.metadata},
            )
            for document in documents
        ]

        for start in range(0, len(points), _UPSERT_BATCH_SIZE):
            batch = points[start : start + _UPSERT_BATCH_SIZE]
            self._client.upsert(collection_name=self._collection_name, points=batch)

        return len(points)

    def delete_repository(self, repository_id: str, branch: str | None = None) -> None:
        """Remove all points for a repository, optionally scoped to one branch.

        Used both for re-indexing (branch-scoped, so other branches of the
        same repository are untouched) and full repository deletion.
        """

        must = [
            models.FieldCondition(key="repository_id", match=models.MatchValue(value=repository_id))
        ]
        if branch is not None:
            must.append(models.FieldCondition(key="branch", match=models.MatchValue(value=branch)))

        self._client.delete(
            collection_name=self._collection_name,
            points_selector=models.FilterSelector(filter=models.Filter(must=must)),
        )

    def similarity_search(
        self,
        query_text: str,
        *,
        repository_id: str,
        branch: str,
        top_k: int,
    ) -> list[SearchResult]:
        """Semantic search scoped to one repository and branch.

        The repository_id/branch filter is applied at the Qdrant query
        level, not after the fact, so repository A can never see repository
        B's chunks in results.
        """

        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="repository_id", match=models.MatchValue(value=repository_id)
                ),
                models.FieldCondition(key="branch", match=models.MatchValue(value=branch)),
            ]
        )

        response = self._client.query_points(
            collection_name=self._collection_name,
            query=self._embeddings.to_inference_document(query_text),
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )

        results = []
        for point in response.points:
            payload = dict(point.payload or {})
            content = payload.pop(_CONTENT_PAYLOAD_KEY, "")
            results.append(SearchResult(content=content, metadata=payload, score=point.score))
        return results
