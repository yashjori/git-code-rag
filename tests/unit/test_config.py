import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestSettingsValidation:
    def test_chunk_overlap_must_be_smaller_than_chunk_size(self):
        with pytest.raises(ValidationError):
            Settings(chunk_size=100, chunk_overlap=100, _env_file=None)

    def test_valid_chunk_configuration(self):
        settings = Settings(chunk_size=1500, chunk_overlap=200, _env_file=None)
        assert settings.chunk_size == 1500
        assert settings.chunk_overlap == 200

    def test_is_groq_configured_false_when_missing(self):
        settings = Settings(groq_api_key="", groq_model="", _env_file=None)
        assert settings.is_groq_configured is False

    def test_is_groq_configured_true_when_both_set(self):
        settings = Settings(groq_api_key="key", groq_model="model", _env_file=None)
        assert settings.is_groq_configured is True

    def test_is_qdrant_configured_requires_dimension(self):
        settings = Settings(
            qdrant_url="https://example.qdrant.io",
            qdrant_embedding_model="sentence-transformers/all-minilm-l6-v2",
            qdrant_embedding_dimension=0,
            _env_file=None,
        )
        assert settings.is_qdrant_configured is False

    def test_is_qdrant_configured_true_when_fully_set(self):
        settings = Settings(
            qdrant_url="https://example.qdrant.io",
            qdrant_embedding_model="sentence-transformers/all-minilm-l6-v2",
            qdrant_embedding_dimension=384,
            _env_file=None,
        )
        assert settings.is_qdrant_configured is True
