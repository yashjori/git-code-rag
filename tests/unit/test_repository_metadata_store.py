from pathlib import Path

from app.models.repository import RepositoryMetadataStore, RepositoryRecord


def _record(repository_id: str, indexed_at: str) -> RepositoryRecord:
    return RepositoryRecord(
        repository_id=repository_id,
        provider="github",
        repository_url=f"https://github.com/example/{repository_id}",
        branch="main",
        local_path=f"/tmp/{repository_id}",
        indexed_at=indexed_at,
        files_indexed=1,
        chunks_created=2,
        status="indexed",
    )


class TestRepositoryMetadataStore:
    def test_upsert_then_get(self, tmp_path: Path):
        store = RepositoryMetadataStore(tmp_path / "repos.db")
        store.upsert(_record("repo-a", "2026-01-01T00:00:00+00:00"))

        record = store.get("repo-a")

        assert record is not None
        assert record.repository_id == "repo-a"
        assert record.status == "indexed"

    def test_get_missing_returns_none(self, tmp_path: Path):
        store = RepositoryMetadataStore(tmp_path / "repos.db")
        assert store.get("does-not-exist") is None

    def test_upsert_is_idempotent_by_repository_id(self, tmp_path: Path):
        store = RepositoryMetadataStore(tmp_path / "repos.db")
        store.upsert(_record("repo-a", "2026-01-01T00:00:00+00:00"))
        updated = _record("repo-a", "2026-01-02T00:00:00+00:00")
        store.upsert(updated)

        assert len(store.list_all()) == 1
        assert store.get("repo-a").indexed_at == "2026-01-02T00:00:00+00:00"

    def test_delete_removes_record(self, tmp_path: Path):
        store = RepositoryMetadataStore(tmp_path / "repos.db")
        store.upsert(_record("repo-a", "2026-01-01T00:00:00+00:00"))
        store.delete("repo-a")
        assert store.get("repo-a") is None

    def test_list_all_returns_every_record(self, tmp_path: Path):
        store = RepositoryMetadataStore(tmp_path / "repos.db")
        store.upsert(_record("repo-a", "2026-01-01T00:00:00+00:00"))
        store.upsert(_record("repo-b", "2026-01-02T00:00:00+00:00"))

        ids = {r.repository_id for r in store.list_all()}

        assert ids == {"repo-a", "repo-b"}

    def test_list_all_empty_store(self, tmp_path: Path):
        store = RepositoryMetadataStore(tmp_path / "repos.db")
        assert store.list_all() == []
