"""One-time git credential injection via environment variables.

Deliberately does NOT embed tokens in the clone URL the way a naive
`https://{token}@host/...` does: git persists a URL-embedded credential
into the cloned repository's local .git/config (verified empirically), so
a stray filesystem read of a cloned repo would leak that user's token.

GIT_CONFIG_COUNT / GIT_CONFIG_KEY_n / GIT_CONFIG_VALUE_n (Git 2.31+) are
documented environment variables that inject a config value for a single
git invocation only - never written to any file. Used here to attach a
one-time HTTP Authorization header, mirroring what git would generate from
a URL-embedded credential, without the on-disk persistence.
"""

from __future__ import annotations

import base64
import os


def build_auth_env(username: str, token: str) -> dict[str, str]:
    """Environment for a single git subprocess call, authenticated as
    (username, token) via a Basic auth header that is never persisted."""

    basic = base64.b64encode(f"{username}:{token}".encode()).decode()
    return {
        **os.environ,
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "http.extraheader",
        "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {basic}",
    }
