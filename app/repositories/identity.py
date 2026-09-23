"""Repository URL parsing and stable repository ID generation.

Kept separate from the provider classes so it can be unit tested without
touching the filesystem or network (repository URL/provider parsing and
repository ID creation are both called out explicitly as unit-test targets).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.exceptions import InvalidRequestError, UnsupportedProviderError

_SLUG_INVALID_CHARS = re.compile(r"[^a-z0-9]+")

GITHUB_HTTPS_RE = re.compile(
    r"^https://github\.com/(?P<org>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$"
)
GITHUB_SSH_RE = re.compile(
    r"^git@github\.com:(?P<org>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$"
)
AZURE_DEVOPS_HTTPS_RE = re.compile(
    r"^https://dev\.azure\.com/(?P<org>[^/]+)/(?P<project>[^/]+)/_git/(?P<repo>[^/?]+)/?"
)

SUPPORTED_PROVIDERS = frozenset({"github", "azure_devops"})


@dataclass(frozen=True)
class RepositoryReference:
    """Everything needed to identify and clone one repository + branch."""

    provider: str
    repository_url: str
    branch: str
    repository_id: str


def slugify(value: str) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", value.strip().lower()).strip("-")
    if not slug:
        raise InvalidRequestError(f"Could not derive an identifier from '{value}'")
    return slug


def parse_github_url(repository_url: str) -> tuple[str, str]:
    """Return (org, repo) for a GitHub HTTPS or SSH URL."""

    match = GITHUB_HTTPS_RE.match(repository_url) or GITHUB_SSH_RE.match(repository_url)
    if not match:
        raise InvalidRequestError(
            "Unrecognized GitHub repository URL. Expected "
            "https://github.com/<org>/<repo> or git@github.com:<org>/<repo>.git"
        )
    return match.group("org"), match.group("repo")


def parse_azure_devops_url(repository_url: str) -> tuple[str, str, str]:
    """Return (organization, project, repository) for an Azure DevOps URL."""

    match = AZURE_DEVOPS_HTTPS_RE.match(repository_url)
    if not match:
        raise InvalidRequestError(
            "Unrecognized Azure DevOps repository URL. Expected "
            "https://dev.azure.com/<organization>/<project>/_git/<repository>"
        )
    return match.group("org"), match.group("project"), match.group("repo")


def build_repository_reference(
    provider: str, repository_url: str, branch: str
) -> RepositoryReference:
    """Validate input and derive a stable, human-readable repository_id.

    The id is deterministic (not a random UUID) so that submitting the same
    provider/URL again for indexing resolves to the same repository_id and
    can be refreshed in place, per the re-indexing requirement.
    """

    if not repository_url or not repository_url.strip():
        raise InvalidRequestError("repository_url must not be empty")
    if not branch or not branch.strip():
        raise InvalidRequestError("branch must not be empty")

    if provider == "github":
        org, repo = parse_github_url(repository_url)
        repository_id = f"github-{slugify(org)}-{slugify(repo)}"
    elif provider == "azure_devops":
        org, project, repo = parse_azure_devops_url(repository_url)
        repository_id = f"azure-{slugify(org)}-{slugify(project)}-{slugify(repo)}"
    else:
        raise UnsupportedProviderError(
            f"Unsupported provider '{provider}'. Supported providers: "
            f"{sorted(SUPPORTED_PROVIDERS)}"
        )

    return RepositoryReference(
        provider=provider,
        repository_url=repository_url,
        branch=branch.strip(),
        repository_id=repository_id,
    )
