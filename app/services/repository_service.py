"""Repository indexing orchestration.

Wires the provider factory, ingestion pipeline, and vector store together.
This is the "indexing pipeline" the spec describes: everything before this
service is provider-specific or purely local; everything it calls after
cloning is provider-agnostic.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import BranchNotIndexedError, RepositoryNotFoundError
from app.core.logging import get_logger
from app.ingestion.pipeline import build_documents_for_repository
from app.models.repository import RepositoryMetadataStore, RepositoryRecord
from app.repositories.factory import create_provider, create_repository_reference
from app.vectorstore.qdrant_store import QdrantVectorStoreService

logger = get_logger(__name__)


@dataclass(frozen=True)
class IndexRepositoryResult:
    repository_id: str
    status: str
    files_scanned: int
    files_indexed: int
    chunks_created: int
    branch: str


class RepositoryService:
    def __init__(
        self,
        settings: Settings,
        vector_store_provider: Callable[[], QdrantVectorStoreService],
        metadata_store: RepositoryMetadataStore,
    ) -> None:
        """vector_store_provider is a lazy factory (e.g. a cached getter),
        not a constructed instance, so that read-only operations (status
        lookup, branch validation) never require Qdrant to be configured -
        only index_repository and delete_repository actually call it."""

        self._settings = settings
        self._vector_store_provider = vector_store_provider
        self._metadata_store = metadata_store

    def index_repository(
        self,
        provider: str,
        repository_url: str,
        branch: str,
        access_token: str | None = None,
    ) -> IndexRepositoryResult:
        reference = create_repository_reference(provider, repository_url, branch)
        repo_provider = create_provider(reference, self._settings, access_token=access_token)
        local_path = repo_provider.clone_repository()

        documents, stats = build_documents_for_repository(local_path, reference, self._settings)

        vector_store = self._vector_store_provider()
        vector_store.ensure_collection(self._settings.qdrant_embedding_dimension)
        # Full-replacement re-indexing (per spec): drop this repository's
        # prior vectors for this branch before writing the fresh set, so a
        # re-index never leaves stale chunks behind.
        vector_store.delete_repository(reference.repository_id, branch=reference.branch)
        if documents:
            vector_store.add_documents(documents)

        self._metadata_store.upsert(
            RepositoryRecord(
                repository_id=reference.repository_id,
                provider=reference.provider,
                repository_url=reference.repository_url,
                branch=reference.branch,
                local_path=str(local_path),
                indexed_at=datetime.now(timezone.utc).isoformat(),
                files_indexed=stats.files_indexed,
                chunks_created=stats.chunks_created,
                status="indexed",
            )
        )

        logger.info(
            "indexing completed: repository_id=%s files_indexed=%d chunks_created=%d",
            reference.repository_id,
            stats.files_indexed,
            stats.chunks_created,
        )

        return IndexRepositoryResult(
            repository_id=reference.repository_id,
            status="indexed",
            files_scanned=stats.files_scanned,
            files_indexed=stats.files_indexed,
            chunks_created=stats.chunks_created,
            branch=reference.branch,
        )

    def get_status(self, repository_id: str) -> RepositoryRecord:
        record = self._metadata_store.get(repository_id)
        if record is None:
            raise RepositoryNotFoundError(f"No indexed repository with id '{repository_id}'")
        return record

    def list_repositories(self) -> list[RepositoryRecord]:
        return self._metadata_store.list_all()

    def delete_repository(self, repository_id: str) -> None:
        record = self._metadata_store.get(repository_id)
        if record is None:
            raise RepositoryNotFoundError(f"No indexed repository with id '{repository_id}'")

        self._vector_store_provider().delete_repository(repository_id)
        self._metadata_store.delete(repository_id)

        local_path = Path(record.local_path)
        storage_root = self._settings.repository_storage_directory
        if local_path.exists() and storage_root in local_path.resolve().parents:
            shutil.rmtree(local_path)

    def validate_repository_branch(self, repository_id: str, branch: str) -> None:
        """Used by the RAG graph's validate_query node."""

        record = self._metadata_store.get(repository_id)
        if record is None:
            raise RepositoryNotFoundError(f"No indexed repository with id '{repository_id}'")
        if record.branch != branch:
            raise BranchNotIndexedError(
                f"Repository '{repository_id}' is indexed for branch "
                f"'{record.branch}', not '{branch}'"
            )
