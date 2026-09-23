import base64

from app.repositories.git_auth import build_auth_env


class TestBuildAuthEnv:
    def test_produces_git_config_override_vars(self):
        env = build_auth_env("x-access-token", "secret-token")
        assert env["GIT_CONFIG_COUNT"] == "1"
        assert env["GIT_CONFIG_KEY_0"] == "http.extraheader"
        assert env["GIT_CONFIG_VALUE_0"].startswith("AUTHORIZATION: basic ")

    def test_header_value_is_correct_basic_auth_encoding(self):
        env = build_auth_env("pat", "my-token")
        encoded = env["GIT_CONFIG_VALUE_0"].removeprefix("AUTHORIZATION: basic ")
        decoded = base64.b64decode(encoded).decode()
        assert decoded == "pat:my-token"

    def test_preserves_existing_environment(self):
        env = build_auth_env("x-access-token", "secret-token")
        # The real process environment (e.g. PATH) must still be present so
        # the git subprocess can actually run.
        assert "PATH" in env

    def test_token_value_itself_is_not_a_plain_top_level_value(self):
        # The raw token must never appear un-encoded anywhere in the env
        # dict values (defense against accidentally logging os.environ).
        env = build_auth_env("pat", "super-secret-raw-token")
        assert "super-secret-raw-token" not in env.values()
