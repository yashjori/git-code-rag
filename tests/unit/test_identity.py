import pytest

from app.core.exceptions import InvalidRequestError, UnsupportedProviderError
from app.repositories.identity import (
    build_repository_reference,
    parse_azure_devops_url,
    parse_github_url,
)


class TestParseGithubUrl:
    def test_https_url(self):
        assert parse_github_url("https://github.com/octocat/Hello-World") == (
            "octocat",
            "Hello-World",
        )

    def test_https_url_with_git_suffix(self):
        assert parse_github_url("https://github.com/octocat/Hello-World.git") == (
            "octocat",
            "Hello-World",
        )

    def test_ssh_url(self):
        assert parse_github_url("git@github.com:octocat/Hello-World.git") == (
            "octocat",
            "Hello-World",
        )

    def test_invalid_url_raises(self):
        with pytest.raises(InvalidRequestError):
            parse_github_url("https://gitlab.com/octocat/Hello-World")


class TestParseAzureDevOpsUrl:
    def test_valid_url(self):
        assert parse_azure_devops_url(
            "https://dev.azure.com/MyOrg/MyProject/_git/MyRepo"
        ) == ("MyOrg", "MyProject", "MyRepo")

    def test_invalid_url_raises(self):
        with pytest.raises(InvalidRequestError):
            parse_azure_devops_url("https://dev.azure.com/MyOrg/MyRepo")


class TestBuildRepositoryReference:
    def test_github_reference_is_deterministic(self):
        ref1 = build_repository_reference(
            "github", "https://github.com/octocat/Hello-World", "main"
        )
        ref2 = build_repository_reference(
            "github", "https://github.com/octocat/Hello-World", "main"
        )
        assert ref1.repository_id == ref2.repository_id == "github-octocat-hello-world"

    def test_azure_devops_reference_id(self):
        ref = build_repository_reference(
            "azure_devops",
            "https://dev.azure.com/MyOrg/MyProject/_git/MyRepo",
            "main",
        )
        assert ref.repository_id == "azure-myorg-myproject-myrepo"

    def test_unsupported_provider_raises(self):
        with pytest.raises(UnsupportedProviderError):
            build_repository_reference(
                "bitbucket", "https://bitbucket.org/x/y", "main"
            )

    def test_empty_repository_url_raises(self):
        with pytest.raises(InvalidRequestError):
            build_repository_reference("github", "", "main")

    def test_empty_branch_raises(self):
        with pytest.raises(InvalidRequestError):
            build_repository_reference(
                "github", "https://github.com/octocat/Hello-World", ""
            )
