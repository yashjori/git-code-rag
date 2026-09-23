"""Database connection configuration and a tiny in-memory connection."""

import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./sample.db")

_USERS = {
    "alice": {"id": "1", "username": "alice", "password_hash": ""},
}


class Connection:
    """Minimal stand-in for a real database connection/session."""

    def find_user_by_username(self, username: str) -> dict | None:
        return _USERS.get(username)

    def find_user_by_id(self, user_id: str) -> dict | None:
        for user in _USERS.values():
            if user["id"] == user_id:
                return user
        return None


def get_connection() -> Connection:
    """Return the database connection configured via DATABASE_URL."""
    return Connection()
