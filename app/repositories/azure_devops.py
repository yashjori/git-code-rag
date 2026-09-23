"""Azure DevOps repository provider.

Isolated from the GitHub provider on purpose: Azure DevOps Git clone
authentication and URL shape differ from GitHub, but both providers expose
the same clone_repository() -> Path contract to the rest of the pipeline.
"""

from __future__ import annotations

from pathlib import Path

import git

from app.core.exceptions import InvalidRepositoryCredentialsError, RepositoryCloneError
from app.core.logging import get_logger, redact_credentials_in_url
from app.repositories.base import RepositoryProvider
from app.repositories.git_auth import build_auth_env

logger = get_logger(__name__)

# Any non-empty username works for Azure DevOps PAT basic auth; the PAT
# itself is what's checked. See Microsoft's documented convention of
# https://<user>:<token>@dev.azure.com/... for Git-over-HTTPS with a PAT.
_PAT_USERNAME = "pat"


class AzureDevOpsProvider(RepositoryProvider):
    """Clones Azure DevOps Git repositories using a Personal Access Token."""

    def __init__(self, *args, azure_devops_pat: str = "", **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._pat = azure_devops_pat

    def _clone_env(self) -> dict[str, str] | None:
        if not self._pat:
            return None
        return build_auth_env(_PAT_USERNAME, self._pat)

    def clone_repository(self) -> Path:
        safe_url = redact_credentials_in_url(self.reference.repository_url)
        branch = self.reference.branch
        logger.info("repository clone started: %s (branch=%s)", safe_url, branch)

        self._reset_local_path()

        try:
            git.Repo.clone_from(
                self.reference.repository_url,
                self.local_path,
                branch=branch,
                depth=1,
                single_branch=True,
                env=self._clone_env(),
            )
        except git.GitCommandError as exc:
            status = getattr(exc, "status", None)
            stderr = (getattr(exc, "stderr", "") or "").lower()
            if status in (401, 403) or "authentication" in stderr:
                raise InvalidRepositoryCredentialsError(
                    f"Azure DevOps rejected credentials for {safe_url}. Provide a "
                    "valid access_token in the request, or set AZURE_DEVOPS_PAT, "
                    "with at least Code (read) scope."
                ) from None
            raise RepositoryCloneError(
                f"Failed to clone {safe_url} (branch={branch}): git clone failed. "
                "Check that the organization, project, repository, and branch exist."
            ) from None

        logger.info("repository clone completed: %s", safe_url)
        return self.local_path
