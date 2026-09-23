"""FastAPI dependency providers.

Every heavyweight object (Qdrant client, Groq client, SQLite store) is built
once per process via lru_cache and handed out through Depends(), rather
than being constructed per-request.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Cookie

from app.core.auth import SESSION_COOKIE_NAME, decode_session_token
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConfigurationError
from app.embeddings.service import EmbeddingService
from app.llm.groq import create_groq_llm
from app.models.repository import RepositoryMetadataStore
from app.models.user import UserStore
from app.retrieval.retriever import CodeRetriever
from app.services.chat_service import ChatService
from app.services.repository_service import RepositoryService
from app.vectorstore.qdrant_store import QdrantVectorStoreService


@lru_cache
def get_metadata_store() -> RepositoryMetadataStore:
    settings = get_settings()
    return RepositoryMetadataStore(settings.repository_metadata_db_path)


@lru_cache
def get_user_store() -> UserStore:
    settings = get_settings()
    return UserStore(settings.repository_metadata_db_path)


def get_current_user(
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> str:
    """FastAPI dependency that gates a route behind a valid session cookie.

    Add `Depends(get_current_user)` to any route that should require login.
    """

    settings = get_settings()
    if not session:
        raise AuthenticationError("Not authenticated")
    return decode_session_token(session, secret_key=settings.auth_secret_key)


@lru_cache
def get_embedding_service() -> EmbeddingService:
    settings = get_settings()
    if not settings.is_qdrant_configured:
        raise ConfigurationError(
            "QDRANT_URL, QDRANT_EMBEDDING_MODEL, and QDRANT_EMBEDDING_DIMENSION must be set"
        )
    return EmbeddingService(settings.qdrant_embedding_model)


@lru_cache
def get_vector_store() -> QdrantVectorStoreService:
    settings = get_settings()
    return QdrantVectorStoreService(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection_name=settings.qdrant_collection_name,
        embedding_service=get_embedding_service(),
    )


@lru_cache
def get_repository_service() -> RepositoryService:
    settings = get_settings()
    return RepositoryService(settings, get_vector_store, get_metadata_store())


@lru_cache
def get_llm():
    settings = get_settings()
    if not settings.is_groq_configured:
        raise ConfigurationError("GROQ_API_KEY and GROQ_MODEL must be set")
    return create_groq_llm(api_key=settings.groq_api_key, model=settings.groq_model)


@lru_cache
def get_retriever() -> CodeRetriever:
    settings = get_settings()
    return CodeRetriever(get_vector_store(), settings.retrieval_top_k)


@lru_cache
def get_chat_service() -> ChatService:
    return ChatService(get_repository_service(), get_retriever(), get_llm())
