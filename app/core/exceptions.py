"""Application-specific exceptions.

Each exception carries the HTTP status code it should map to. The FastAPI
exception handler (registered in app.main) turns these into JSON error
responses. Messages must never contain tokens, PATs, or unredacted Git
URLs - callers are responsible for passing already-sanitized text.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for all application-raised errors."""

    http_status: int = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidRequestError(AppError):
    """Malformed or semantically invalid request input."""

    http_status = 400


class ConfigurationError(AppError):
    """Required configuration (Groq, Qdrant, auth) is missing."""

    http_status = 503


class AuthenticationError(AppError):
    """Missing, invalid, or expired session; or bad login credentials."""

    http_status = 401


class UnsupportedProviderError(InvalidRequestError):
    """Requested repository provider is not implemented."""


class InvalidRepositoryCredentialsError(AppError):
    """Git provider rejected the configured credentials, or none were
    supplied for a private repository."""

    http_status = 401


class RepositoryNotFoundError(AppError):
    """No indexed repository matches the given repository_id."""

    http_status = 404


class BranchNotIndexedError(AppError):
    """The repository is indexed, but not for the requested branch."""

    http_status = 404


class RepositoryCloneError(AppError):
    """Cloning or refreshing the repository failed."""

    http_status = 502


class IngestionError(AppError):
    """Scanning, chunking, embedding, or storing a repository failed."""

    http_status = 500


class GraphExecutionError(AppError):
    """The LangGraph RAG workflow failed to complete."""

    http_status = 500
