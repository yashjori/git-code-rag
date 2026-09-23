"""SQLite-backed repository metadata store.

A full relational database is unnecessary for V1 (per spec); SQLite via the
standard library is simple and reliable for the small amount of metadata
tracked per indexed repository. Never stores authentication tokens - only
the plain repository_url, which callers must not embed credentials into.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RepositoryRecord:
    repository_id: str
    provider: str
    repository_url: str
    branch: str
    local_path: str
    indexed_at: str
    files_indexed: int
    chunks_created: int
    status: str


_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS repositories (
    repository_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    repository_url TEXT NOT NULL,
    branch TEXT NOT NULL,
    local_path TEXT NOT NULL,
    indexed_at TEXT NOT NULL,
    files_indexed INTEGER NOT NULL,
    chunks_created INTEGER NOT NULL,
    status TEXT NOT NULL
)
"""


class RepositoryMetadataStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE_SQL)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def upsert(self, record: RepositoryRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO repositories (
                    repository_id, provider, repository_url, branch,
                    local_path, indexed_at, files_indexed, chunks_created, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(repository_id) DO UPDATE SET
                    provider=excluded.provider,
                    repository_url=excluded.repository_url,
                    branch=excluded.branch,
                    local_path=excluded.local_path,
                    indexed_at=excluded.indexed_at,
                    files_indexed=excluded.files_indexed,
                    chunks_created=excluded.chunks_created,
                    status=excluded.status
                """,
                (
                    record.repository_id,
                    record.provider,
                    record.repository_url,
                    record.branch,
                    record.local_path,
                    record.indexed_at,
                    record.files_indexed,
                    record.chunks_created,
                    record.status,
                ),
            )

    def get(self, repository_id: str) -> RepositoryRecord | None:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM repositories WHERE repository_id = ?", (repository_id,)
            ).fetchone()
        if row is None:
            return None
        return RepositoryRecord(**dict(row))

    def delete(self, repository_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM repositories WHERE repository_id = ?", (repository_id,))

    def list_all(self) -> list[RepositoryRecord]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM repositories ORDER BY indexed_at DESC"
            ).fetchall()
        return [RepositoryRecord(**dict(row)) for row in rows]
