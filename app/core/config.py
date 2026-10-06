"""Application configuration.

All environment-dependent values are read here through pydantic-settings.
No module outside this file should read `os.environ` directly, and no
model name (Groq or Qdrant embedding) is hardcoded anywhere else in the
codebase.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Source file extensions worth indexing for code understanding.
CODE_FILE_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".cs",
        ".go",
        ".rs",
        ".cpp",
        ".cc",
        ".c",
        ".h",
        ".hpp",
        ".sql",
    }
)

# Documentation/config files worth indexing for repository understanding.
DOC_AND_CONFIG_FILE_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".md",
        ".txt",
        ".yml",
        ".yaml",
        ".json",
        ".toml",
    }
)

# Filenames (not extensions) that are always worth indexing when present.
ALWAYS_INDEX_FILENAMES: frozenset[str] = frozenset(
    {
        "Dockerfile",
        "docker-compose.yml",
        "requirements.txt",
        "pyproject.toml",
        "package.json",
    }
)

SUPPORTED_FILE_EXTENSIONS: frozenset[str] = (
    CODE_FILE_EXTENSIONS | DOC_AND_CONFIG_FILE_EXTENSIONS
)

# Directories never worth walking into: build output, dependency caches,
# VCS internals, and IDE state. Matched by directory name anywhere in the
# path, not just at the repository root.
IGNORED_DIRECTORY_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".github",
        ".idea",
        ".vscode",
        "node_modules",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "dist",
        "build",
        "coverage",
        "target",
        ".next",
        "out",
        "vendor",
    }
)

# Suffixes for generated/compiled/binary artifacts that are never source.
IGNORED_FILE_SUFFIXES: frozenset[str] = frozenset(
    {
        ".pyc",
        ".class",
        ".jar",
        ".min.js",
        ".map",
        ".lock",
        # binary / media / archive formats
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".ico",
        ".webp",
        ".svg",
        ".mp4",
        ".mov",
        ".avi",
        ".mp3",
        ".wav",
        ".zip",
        ".tar",
        ".gz",
        ".7z",
        ".rar",
        ".whl",
        ".so",
        ".dylib",
        ".dll",
        ".exe",
        ".bin",
        ".pdf",
    }
)


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Git Repository Code Assistant"
    app_env: str = "development"
    log_level: str = "INFO"
    # Comma-separated list of origins the frontend is served from, e.g.
    # "http://localhost:5173,https://assistant.example.com".
    cors_allowed_origins: str = "http://localhost:5173"

    # Session auth. auth_secret_key signs session JWTs - must be a real
    # random value in any deployment that isn't purely local (a weak or
    # shared key lets anyone forge a session). cookie_secure should be
    # true whenever served over HTTPS (the browser refuses to send a
    # Secure cookie over plain HTTP, so this must be false for local dev).
    auth_secret_key: str = ""
    auth_session_days: int = 7
    cookie_secure: bool = True

    # Optional login account created at startup if it doesn't exist yet -
    # for hosts with an ephemeral filesystem and no shell (e.g. Render's
    # free tier), where app/scripts/create_user.py can't be run. Takes a
    # bcrypt hash, never a plain-text password.
    bootstrap_admin_username: str = ""
    bootstrap_admin_password_hash: str = ""

    # Groq (generation LLM only)
    groq_api_key: str = ""
    groq_model: str = ""

    # Git provider credentials
    github_token: str = ""
    azure_devops_pat: str = ""

    # Qdrant Cloud (hosted vector store + hosted embedding inference)
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection_name: str = "code_chunks"
    qdrant_embedding_model: str = ""
    # Qdrant Cloud Inference does not expose model dimensionality through
    # the client API - it's only shown in the cluster's Inference tab in
    # the Qdrant Cloud console. The collection must be created with the
    # correct vector size up front, so this is required configuration
    # alongside the model name rather than something the app can infer.
    qdrant_embedding_dimension: int = 0

    # Local repository processing
    repository_storage_directory: Path = Path("./data/repositories")
    repository_metadata_db_path: Path = Path("./data/repositories.db")

    chunk_size: int = 1500
    chunk_overlap: int = 200
    retrieval_top_k: int = 8
    max_index_file_size_kb: int = 512

    @field_validator("repository_storage_directory", "repository_metadata_db_path")
    @classmethod
    def _resolve_path(cls, value: Path) -> Path:
        return value.expanduser().resolve()

    @field_validator("chunk_overlap")
    @classmethod
    def _overlap_smaller_than_chunk(cls, value: int, info) -> int:
        chunk_size = info.data.get("chunk_size")
        if chunk_size is not None and value >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def is_groq_configured(self) -> bool:
        return bool(self.groq_api_key and self.groq_model)

    @property
    def is_qdrant_configured(self) -> bool:
        return bool(
            self.qdrant_url and self.qdrant_embedding_model and self.qdrant_embedding_dimension > 0
        )

    @property
    def is_auth_configured(self) -> bool:
        # A short/default key would make sessions forgeable, so require a
        # real amount of entropy rather than just "non-empty".
        return len(self.auth_secret_key) >= 32


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide cached Settings instance."""

    return Settings()
