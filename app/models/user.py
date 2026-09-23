"""SQLite-backed user store.

Same pattern as RepositoryMetadataStore. Passwords are never stored in
plain text - only a bcrypt hash. There is no open self-registration
endpoint; accounts are created directly against this store (see
app/scripts/create_user.py), since an open signup form on an app that
calls paid-per-use Groq/Qdrant APIs would just be a new abuse vector.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class UserRecord:
    username: str
    password_hash: str
    created_at: str


_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


class UserStore:
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

    def create(self, record: UserRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (record.username, record.password_hash, record.created_at),
            )

    def get(self, username: str) -> UserRecord | None:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
        if row is None:
            return None
        return UserRecord(**dict(row))
