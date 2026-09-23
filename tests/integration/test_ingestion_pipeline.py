"""sample local repository -> ingestion pipeline, no network calls."""

from pathlib import Path

from app.core.config import get_settings
from app.ingestion.pipeline import build_documents_for_repository
from app.repositories.identity import build_repository_reference

SAMPLE_REPO = Path(__file__).parent.parent / "fixtures" / "sample_repo"


def test_sample_repository_is_scanned_and_chunked():
    settings = get_settings()
    reference = build_repository_reference(
        "github", "https://github.com/example/sample-repo", "main"
    )

    documents, stats = build_documents_for_repository(SAMPLE_REPO, reference, settings)

    assert stats.files_scanned >= stats.files_indexed > 0
    assert stats.chunks_created == len(documents)
    assert stats.chunks_created > 0


def test_every_document_has_required_metadata_fields():
    settings = get_settings()
    reference = build_repository_reference(
        "github", "https://github.com/example/sample-repo", "main"
    )
    documents, _ = build_documents_for_repository(SAMPLE_REPO, reference, settings)

    required_fields = {
        "repository_id",
        "provider",
        "branch",
        "file_path",
        "file_name",
        "language",
        "chunk_index",
        "start_line",
        "end_line",
        "symbol_name",
        "symbol_type",
    }
    for document in documents:
        assert required_fields.issubset(document.metadata.keys())
        assert document.metadata["repository_id"] == reference.repository_id
        assert document.metadata["branch"] == "main"
        assert document.page_content.strip() != ""


def test_jwt_module_is_indexed_with_create_access_token_symbol():
    settings = get_settings()
    reference = build_repository_reference(
        "github", "https://github.com/example/sample-repo", "main"
    )
    documents, _ = build_documents_for_repository(SAMPLE_REPO, reference, settings)

    jwt_docs = [d for d in documents if d.metadata["file_path"] == "app/auth/jwt.py"]
    assert jwt_docs
    symbol_names = {d.metadata["symbol_name"] for d in jwt_docs}
    assert "create_access_token" in symbol_names


def test_ignored_and_binary_files_are_excluded():
    settings = get_settings()
    reference = build_repository_reference(
        "github", "https://github.com/example/sample-repo", "main"
    )
    documents, _ = build_documents_for_repository(SAMPLE_REPO, reference, settings)

    file_paths = {d.metadata["file_path"] for d in documents}
    assert "app/__init__.py" not in file_paths  # empty file, no chunks
    assert all(not path.startswith(".git/") for path in file_paths)
