from pathlib import Path

import pytest

from app.core.exceptions import UsernameTakenError
from app.models.user import UserRecord, UserStore


def _record(username: str) -> UserRecord:
    return UserRecord(
        username=username,
        password_hash="$2b$12$fakehashfakehashfakehashfakehashfakehashfakehashfak",
        created_at="2026-01-01T00:00:00+00:00",
    )


class TestUserStore:
    def test_create_then_get(self, tmp_path: Path):
        store = UserStore(tmp_path / "users.db")
        store.create(_record("alice"))

        user = store.get("alice")

        assert user is not None
        assert user.username == "alice"

    def test_get_missing_returns_none(self, tmp_path: Path):
        store = UserStore(tmp_path / "users.db")
        assert store.get("nobody") is None

    def test_duplicate_username_raises(self, tmp_path: Path):
        store = UserStore(tmp_path / "users.db")
        store.create(_record("alice"))
        with pytest.raises(UsernameTakenError):
            store.create(_record("alice"))
