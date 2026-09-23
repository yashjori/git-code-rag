"""Password hashing and session token (JWT) helpers.

Sessions are an HttpOnly cookie carrying a signed JWT - not accessible to
page JavaScript (so an XSS bug can't steal it the way a localStorage token
could), and not sent to nginx to check (auth is fully backend-owned; see
app/api/dependencies.py's get_current_user).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.exceptions import AuthenticationError

SESSION_COOKIE_NAME = "gca_session"
_JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_session_token(username: str, *, secret_key: str, expires_in_days: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(days=expires_in_days),
    }
    return jwt.encode(payload, secret_key, algorithm=_JWT_ALGORITHM)


def decode_session_token(token: str, *, secret_key: str) -> str:
    """Return the username carried by a valid, unexpired session token."""

    try:
        payload = jwt.decode(token, secret_key, algorithms=[_JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        raise AuthenticationError("Session is invalid or has expired") from None
    return payload["sub"]
