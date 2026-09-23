"""Authentication routes: login, logout, current-user check.

No self-registration endpoint here on purpose - see app/models/user.py.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.api.dependencies import get_current_user, get_user_store
from app.core.auth import SESSION_COOKIE_NAME, create_session_token, hash_password, verify_password
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConfigurationError
from app.models.schemas import CurrentUserResponse, LoginRequest
from app.models.user import UserStore

router = APIRouter()

# Compared against on every failed lookup so a login attempt for a
# username that doesn't exist takes about as long as one that does -
# otherwise response timing would leak which usernames are registered.
_DUMMY_PASSWORD_HASH = hash_password("not-a-real-password-used-only-for-timing")


@router.post("/login", response_model=CurrentUserResponse)
def login(
    request: LoginRequest,
    response: Response,
    user_store: UserStore = Depends(get_user_store),
) -> CurrentUserResponse:
    settings = get_settings()
    if not settings.is_auth_configured:
        raise ConfigurationError("AUTH_SECRET_KEY must be set (32+ characters) to issue sessions")

    user = user_store.get(request.username)
    password_hash = user.password_hash if user else _DUMMY_PASSWORD_HASH
    password_ok = verify_password(request.password, password_hash)

    if user is None or not password_ok:
        raise AuthenticationError("Incorrect username or password")

    token = create_session_token(
        user.username,
        secret_key=settings.auth_secret_key,
        expires_in_days=settings.auth_session_days,
    )
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.auth_session_days * 24 * 60 * 60,
    )
    return CurrentUserResponse(username=user.username)


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"status": "logged_out"}


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: str = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse(username=current_user)
