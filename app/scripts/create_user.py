"""Create a login account.

    uv run python -m app.scripts.create_user <username>

Deliberately never accepts a password as a command-line argument or env
var - one would leak into shell history and the process list. Generates a
random one and prints it exactly once.
"""

from __future__ import annotations

import secrets
import sys
from datetime import datetime, timezone

from app.core.auth import hash_password
from app.core.config import get_settings
from app.models.user import UserRecord, UserStore


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python -m app.scripts.create_user <username>", file=sys.stderr)
        sys.exit(1)

    username = sys.argv[1]
    settings = get_settings()
    store = UserStore(settings.repository_metadata_db_path)

    if store.get(username) is not None:
        print(f"user '{username}' already exists", file=sys.stderr)
        sys.exit(1)

    password = secrets.token_urlsafe(15)
    store.create(
        UserRecord(
            username=username,
            password_hash=hash_password(password),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )
    print(f"created user '{username}'")
    print(f"password: {password}")


if __name__ == "__main__":
    main()
