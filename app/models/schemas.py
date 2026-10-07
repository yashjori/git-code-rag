"""API request/response schemas.

Kept separate from service logic per the spec's coding expectations: routes
and services work with these Pydantic models and with plain dataclasses
from the service layer, never with each other's internals directly.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class SignupRequest(BaseModel):
    # Letters, digits, dot, dash, underscore - keeps usernames safe to show
    # verbatim in the UI and logs.
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9._-]+$")
    # bcrypt silently ignores everything past 72 bytes, so cap it rather
    # than let two different long passwords hash identically.
    password: str = Field(min_length=8, max_length=72)


class CurrentUserResponse(BaseModel):
    username: str


class IndexRepositoryRequest(BaseModel):
    provider: Literal["github", "azure_devops"]
    repository_url: str = Field(min_length=1)
    branch: str = Field(default="main", min_length=1)
    # Optional per-request credential (GitHub PAT / Azure DevOps PAT) for a
    # private repository. Used once for this clone, then discarded: never
    # logged, never stored in repository metadata, never returned in any
    # response. Falls back to the server's default GITHUB_TOKEN /
    # AZURE_DEVOPS_PAT when omitted.
    access_token: str | None = Field(default=None, min_length=1)


class IndexRepositoryResponse(BaseModel):
    repository_id: str
    status: str
    files_scanned: int
    files_indexed: int
    chunks_created: int
    branch: str


class RepositoryStatusResponse(BaseModel):
    repository_id: str
    provider: str
    repository_url: str
    branch: str
    indexed_at: str
    files_indexed: int
    chunks_created: int
    status: str


class RepositoryListResponse(BaseModel):
    repositories: list[RepositoryStatusResponse]


class DeleteRepositoryResponse(BaseModel):
    repository_id: str
    status: Literal["deleted"]


class ChatQueryRequest(BaseModel):
    repository_id: str = Field(min_length=1)
    branch: str = Field(default="main", min_length=1)
    question: str = Field(min_length=1)


class SourceReference(BaseModel):
    file_path: str
    start_line: int
    end_line: int


class ChatQueryResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
    repository_id: str
