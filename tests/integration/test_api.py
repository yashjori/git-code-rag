"""FastAPI route tests with dependency overrides.

No real Qdrant or Groq calls: get_repository_service and get_chat_service
are overridden with fakes, so this suite runs the full request/response
cycle (routing, Pydantic validation, exception handling) without network
access or credentials.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_chat_service, get_current_user, get_repository_service
from app.core.exceptions import RepositoryNotFoundError
from app.main import app
from app.models.repository import RepositoryRecord
from app.repositories.identity import build_repository_reference
from app.services.chat_service import ChatResult
from app.services.repository_service import IndexRepositoryResult


class FakeRepositoryService:
    def __init__(self):
        self._records: dict[str, RepositoryRecord] = {}

    def index_repository(self, provider, repository_url, branch, access_token=None):
        reference = build_repository_reference(provider, repository_url, branch)
        self._records[reference.repository_id] = RepositoryRecord(
            repository_id=reference.repository_id,
            provider=reference.provider,
            repository_url=reference.repository_url,
            branch=reference.branch,
            local_path="/tmp/fake",
            indexed_at="2026-01-01T00:00:00+00:00",
            files_indexed=6,
            chunks_created=7,
            status="indexed",
        )
        return IndexRepositoryResult(
            repository_id=reference.repository_id,
            status="indexed",
            files_scanned=8,
            files_indexed=6,
            chunks_created=7,
            branch=reference.branch,
        )

    def get_status(self, repository_id):
        record = self._records.get(repository_id)
        if record is None:
            raise RepositoryNotFoundError(f"No indexed repository with id '{repository_id}'")
        return record

    def list_repositories(self):
        return list(self._records.values())

    def delete_repository(self, repository_id):
        if repository_id not in self._records:
            raise RepositoryNotFoundError(f"No indexed repository with id '{repository_id}'")
        del self._records[repository_id]


class FakeChatService:
    def ask(self, repository_id, branch, question):
        return ChatResult(
            answer=f"Answer for: {question}",
            sources=[{"file_path": "app/auth/jwt.py", "start_line": 8, "end_line": 35}],
            repository_id=repository_id,
        )


@pytest.fixture
def client():
    fake_repository_service = FakeRepositoryService()
    fake_chat_service = FakeChatService()

    app.dependency_overrides[get_repository_service] = lambda: fake_repository_service
    app.dependency_overrides[get_chat_service] = lambda: fake_chat_service
    app.dependency_overrides[get_current_user] = lambda: "test-user"
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client():
    """A client with no get_current_user override - exercises the real
    session-cookie gate on protected routes."""
    fake_repository_service = FakeRepositoryService()
    fake_chat_service = FakeChatService()

    app.dependency_overrides[get_repository_service] = lambda: fake_repository_service
    app.dependency_overrides[get_chat_service] = lambda: fake_chat_service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_index_repository(client):
    response = client.post(
        "/api/v1/repositories/index",
        json={
            "provider": "github",
            "repository_url": "https://github.com/example/backend",
            "branch": "main",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["repository_id"] == "github-example-backend"
    assert body["status"] == "indexed"
    assert body["chunks_created"] == 7


def test_index_repository_rejects_unknown_provider(client):
    response = client.post(
        "/api/v1/repositories/index",
        json={"provider": "gitlab", "repository_url": "https://gitlab.com/a/b", "branch": "main"},
    )
    assert response.status_code == 422


def test_index_repository_accepts_per_request_access_token_and_never_echoes_it(client):
    response = client.post(
        "/api/v1/repositories/index",
        json={
            "provider": "github",
            "repository_url": "https://github.com/example/backend",
            "branch": "main",
            "access_token": "ghp_super_secret_value",
        },
    )
    assert response.status_code == 200
    assert "ghp_super_secret_value" not in response.text


def test_get_repository_status_after_indexing(client):
    client.post(
        "/api/v1/repositories/index",
        json={
            "provider": "github",
            "repository_url": "https://github.com/example/backend",
            "branch": "main",
        },
    )
    response = client.get("/api/v1/repositories/github-example-backend")
    assert response.status_code == 200
    assert response.json()["status"] == "indexed"


def test_list_repositories_empty(client):
    response = client.get("/api/v1/repositories")
    assert response.status_code == 200
    assert response.json() == {"repositories": []}


def test_list_repositories_after_indexing_two(client):
    client.post(
        "/api/v1/repositories/index",
        json={
            "provider": "github",
            "repository_url": "https://github.com/example/backend",
            "branch": "main",
        },
    )
    client.post(
        "/api/v1/repositories/index",
        json={
            "provider": "github",
            "repository_url": "https://github.com/example/frontend",
            "branch": "main",
        },
    )
    response = client.get("/api/v1/repositories")
    assert response.status_code == 200
    ids = {r["repository_id"] for r in response.json()["repositories"]}
    assert ids == {"github-example-backend", "github-example-frontend"}


def test_get_repository_status_unknown_returns_404(client):
    response = client.get("/api/v1/repositories/does-not-exist")
    assert response.status_code == 404


def test_delete_repository_then_status_is_404(client):
    client.post(
        "/api/v1/repositories/index",
        json={
            "provider": "github",
            "repository_url": "https://github.com/example/backend",
            "branch": "main",
        },
    )
    delete_response = client.delete("/api/v1/repositories/github-example-backend")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"repository_id": "github-example-backend", "status": "deleted"}

    status_response = client.get("/api/v1/repositories/github-example-backend")
    assert status_response.status_code == 404


def test_chat_query_returns_answer_and_sources(client):
    response = client.post(
        "/api/v1/chat/query",
        json={
            "repository_id": "github-example-backend",
            "branch": "main",
            "question": "Where is JWT authentication implemented?",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "Where is JWT authentication implemented?" in body["answer"]
    assert body["sources"] == [{"file_path": "app/auth/jwt.py", "start_line": 8, "end_line": 35}]
    assert body["repository_id"] == "github-example-backend"


def test_chat_query_rejects_empty_question(client):
    response = client.post(
        "/api/v1/chat/query",
        json={"repository_id": "github-example-backend", "question": ""},
    )
    assert response.status_code == 422


def test_protected_routes_reject_requests_without_a_session(unauthenticated_client):
    assert unauthenticated_client.get("/api/v1/repositories").status_code == 401
    assert (
        unauthenticated_client.post(
            "/api/v1/repositories/index",
            json={"provider": "github", "repository_url": "https://github.com/a/b", "branch": "main"},
        ).status_code
        == 401
    )
    assert (
        unauthenticated_client.post(
            "/api/v1/chat/query",
            json={"repository_id": "r", "question": "hi"},
        ).status_code
        == 401
    )


def test_me_without_session_is_401(unauthenticated_client):
    response = unauthenticated_client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.fixture
def real_user_store(tmp_path, monkeypatch):
    """A real UserStore + a real, valid AUTH_SECRET_KEY for the process-wide
    cached Settings - the login route reads settings directly, not through
    an overridable dependency, so the secret must actually be present."""
    from app.api.dependencies import get_user_store
    from app.core.config import get_settings
    from app.models.user import UserStore

    settings = get_settings()
    monkeypatch.setattr(settings, "auth_secret_key", "a" * 32)
    monkeypatch.setattr(settings, "cookie_secure", False)

    store = UserStore(tmp_path / "users.db")
    app.dependency_overrides[get_user_store] = lambda: store
    yield store
    del app.dependency_overrides[get_user_store]


def test_login_with_correct_password_sets_session_cookie(unauthenticated_client, real_user_store):
    from app.core.auth import hash_password
    from app.models.user import UserRecord

    real_user_store.create(
        UserRecord(username="alice", password_hash=hash_password("s3cret!"), created_at="2026-01-01")
    )

    response = unauthenticated_client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "s3cret!"}
    )

    assert response.status_code == 200
    assert response.json() == {"username": "alice"}
    assert "gca_session" in response.cookies


def test_login_with_wrong_password_is_401(unauthenticated_client, real_user_store):
    from app.core.auth import hash_password
    from app.models.user import UserRecord

    real_user_store.create(
        UserRecord(username="alice", password_hash=hash_password("s3cret!"), created_at="2026-01-01")
    )

    response = unauthenticated_client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "wrong"}
    )
    assert response.status_code == 401


def test_login_with_unknown_username_is_401(unauthenticated_client, real_user_store):
    response = unauthenticated_client.post(
        "/api/v1/auth/login", json={"username": "nobody", "password": "whatever"}
    )
    assert response.status_code == 401


def test_full_login_flow_grants_access_to_protected_routes(unauthenticated_client, real_user_store):
    from app.core.auth import hash_password
    from app.models.user import UserRecord

    real_user_store.create(
        UserRecord(username="alice", password_hash=hash_password("s3cret!"), created_at="2026-01-01")
    )

    login_response = unauthenticated_client.post(
        "/api/v1/auth/login", json={"username": "alice", "password": "s3cret!"}
    )
    assert login_response.status_code == 200

    me_response = unauthenticated_client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json() == {"username": "alice"}

    repos_response = unauthenticated_client.get("/api/v1/repositories")
    assert repos_response.status_code == 200

    logout_response = unauthenticated_client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200

    after_logout = unauthenticated_client.get("/api/v1/auth/me")
    assert after_logout.status_code == 401
