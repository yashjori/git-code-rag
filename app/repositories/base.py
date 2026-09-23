"""Common repository provider abstraction.

Every provider turns a (repository_url, branch) pair into a local checked-out
directory. Everything downstream (scanning, filtering, chunking, embedding,
storing) works only with that local Path and is entirely provider-agnostic.
"""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from app.repositories.identity import RepositoryReference


class RepositoryProvider(ABC):
    """Base class for a Git hosting provider."""

    def __init__(self, reference: RepositoryReference, storage_root: Path) -> None:
        self.reference = reference
        self.storage_root = storage_root

    @property
    def local_path(self) -> Path:
        """Directory this repository is (or will be) checked out into.

        Always a direct child of storage_root, named after the generated
        repository_id, so a clone can never escape the configured storage
        directory via a crafted repository_id.
        """

        return (self.storage_root / self.reference.repository_id).resolve()

    def _reset_local_path(self) -> None:
        """Remove any prior checkout so the clone starts clean.

        Full replacement is the accepted V1 re-indexing strategy (no
        incremental commit-diff indexing), so the simplest correct approach
        is to discard the previous checkout rather than reconcile it.
        """

        if self.local_path.exists():
            shutil.rmtree(self.local_path)
        self.local_path.parent.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def clone_repository(self) -> Path:
        """Clone (or refresh) the repository and return its local path."""
        raise NotImplementedError
