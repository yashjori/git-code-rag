"""GitHub repository provider."""

from __future__ import annotations

from pathlib import Path

import git

from app.core.exceptions import InvalidRepositoryCredentialsError, RepositoryCloneError
from app.core.logging import get_logger, redact_credentials_in_url
from app.repositories.base import RepositoryProvider
from app.repositories.git_auth import build_auth_env

logger = get_logger(__name__)

# Any non-empty username works for GitHub token auth over HTTPS; GitHub only
# checks the password/token field. x-access-token mirrors the convention
# GitHub Apps installation tokens use.
_AUTH_USERNAME = "x-access-token"


class GitHubProvider(RepositoryProvider):
    """Clones public or token-authenticated private GitHub repositories."""

    def __init__(self, *args, github_token: str = "", **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._github_token = github_token

    def _clone_env(self) -> dict[str, str] | None:
        # Token auth only applies to HTTPS clone URLs; SSH URLs rely on the
        # host's configured SSH keys instead.
        if not self._github_token or not self.reference.repository_url.startswith("https://"):
            return None
        return build_auth_env(_AUTH_USERNAME, self._github_token)

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
            if status in (401, 403) or "authentication" in stderr or "could not read username" in stderr:
                raise InvalidRepositoryCredentialsError(
                    f"GitHub rejected credentials for {safe_url}. Provide a valid "
                    "access_token in the request, or set GITHUB_TOKEN, for "
                    "private repositories."
                ) from None
            raise RepositoryCloneError(
                f"Failed to clone {safe_url} (branch={branch}): git clone failed. "
                "Check that the repository and branch exist."
            ) from None

        logger.info("repository clone completed: %s", safe_url)
        return self.local_path
