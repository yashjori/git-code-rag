"""Authentication business logic."""

from app.auth.jwt import create_access_token
from app.database import get_connection


class AuthenticationError(Exception):
    """Raised when a login attempt fails."""


def authenticate_user(username: str, password: str) -> str:
    """Authenticate a user and return a signed access token.

    Looks up the user by username, checks the password hash, and issues a
    JWT access token on success. Raises AuthenticationError on failure.
    """
    connection = get_connection()
    user = connection.find_user_by_username(username)
    if user is None or not _password_matches(password, user["password_hash"]):
        raise AuthenticationError("invalid username or password")
    return create_access_token(user_id=user["id"])


def _password_matches(password: str, password_hash: str) -> bool:
    return _hash_password(password) == password_hash


def _hash_password(password: str) -> str:
    import hashlib

    return hashlib.sha256(password.encode()).hexdigest()


class UserService:
    """Handles user lookups and profile updates."""

    def __init__(self):
        self.connection = get_connection()

    def get_profile(self, user_id: str) -> dict:
        return self.connection.find_user_by_id(user_id)
