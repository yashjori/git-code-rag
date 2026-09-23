"""Provider factory: the only place that knows which provider class to use.

Adding a third Git host means adding one branch here and one new provider
module; nothing in ingestion/embeddings/vectorstore/retrieval/graph changes.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.exceptions import UnsupportedProviderError
from app.repositories.azure_devops import AzureDevOpsProvider
from app.repositories.base import RepositoryProvider
from app.repositories.github import GitHubProvider
from app.repositories.identity import RepositoryReference, build_repository_reference


def create_repository_reference(
    provider: str, repository_url: str, branch: str
) -> RepositoryReference:
    return build_repository_reference(provider, repository_url, branch)


def create_provider(
    reference: RepositoryReference,
    settings: Settings,
    *,
    access_token: str | None = None,
) -> RepositoryProvider:
    """access_token, when given, overrides the server-wide default token
    from settings for this one clone - lets each caller supply their own
    credential instead of every request sharing one server-configured
    identity. Never persisted; used only for this clone_repository() call."""

    storage_root = settings.repository_storage_directory

    if reference.provider == "github":
        return GitHubProvider(
            reference, storage_root, github_token=access_token or settings.github_token
        )
    if reference.provider == "azure_devops":
        return AzureDevOpsProvider(
            reference, storage_root, azure_devops_pat=access_token or settings.azure_devops_pat
        )

    raise UnsupportedProviderError(f"Unsupported provider '{reference.provider}'")
