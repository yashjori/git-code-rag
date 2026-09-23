"""JWT access token creation and verification."""

import time
import hashlib
import hmac
import json
import base64

_SECRET = "sample-secret-not-for-production"


def create_access_token(user_id: str, expires_in_seconds: int = 3600) -> str:
    """Generate a signed JWT-style access token for a user.

    This is where JWT access tokens are generated for the sample service.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": user_id, "exp": int(time.time()) + expires_in_seconds}
    header_b64 = _b64encode(json.dumps(header))
    payload_b64 = _b64encode(json.dumps(payload))
    signature = _sign(f"{header_b64}.{payload_b64}")
    return f"{header_b64}.{payload_b64}.{signature}"


def verify_access_token(token: str) -> dict | None:
    """Verify a token's signature and expiry, returning its payload."""
    try:
        header_b64, payload_b64, signature = token.split(".")
    except ValueError:
        return None

    expected_signature = _sign(f"{header_b64}.{payload_b64}")
    if not hmac.compare_digest(signature, expected_signature):
        return None

    payload = json.loads(_b64decode(payload_b64))
    if payload["exp"] < time.time():
        return None
    return payload


def _sign(data: str) -> str:
    digest = hmac.new(_SECRET.encode(), data.encode(), hashlib.sha256).digest()
    return _b64encode(digest.decode("latin1"))


def _b64encode(data: str) -> str:
    return base64.urlsafe_b64encode(data.encode("latin1")).decode().rstrip("=")


def _b64decode(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("latin1")
