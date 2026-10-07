"""Authentication routes: sign-up, login, logout, current-user check."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response

from app.api.dependencies import get_current_user, get_user_store
from app.core.auth import SESSION_COOKIE_NAME, create_session_token, hash_password, verify_password
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConfigurationError
from app.models.schemas import CurrentUserResponse, LoginRequest, SignupRequest
from app.models.user import UserRecord, UserStore

router = APIRouter()

# Compared against on every failed lookup so a login attempt for a
# username that doesn't exist takes about as long as one that does -
# otherwise response timing would leak which usernames are registered.
_DUMMY_PASSWORD_HASH = hash_password("not-a-real-password-used-only-for-timing")


def _require_auth_configured() -> None:
    if not get_settings().is_auth_configured:
        raise ConfigurationError("AUTH_SECRET_KEY must be set (32+ characters) to issue sessions")


def _start_session(response: Response, username: str) -> CurrentUserResponse:
    settings = get_settings()
    token = create_session_token(
        username,
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
    return CurrentUserResponse(username=username)


@router.post("/signup", response_model=CurrentUserResponse, status_code=201)
def signup(
    request: SignupRequest,
    response: Response,
    user_store: UserStore = Depends(get_user_store),
) -> CurrentUserResponse:
    _require_auth_configured()
    # UserStore.create raises UsernameTakenError (409) on a duplicate.
    user_store.create(
        UserRecord(
            username=request.username,
            password_hash=hash_password(request.password),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )
    return _start_session(response, request.username)


@router.post("/login", response_model=CurrentUserResponse)
def login(
    request: LoginRequest,
    response: Response,
    user_store: UserStore = Depends(get_user_store),
) -> CurrentUserResponse:
    _require_auth_configured()

    user = user_store.get(request.username)
    password_hash = user.password_hash if user else _DUMMY_PASSWORD_HASH
    password_ok = verify_password(request.password, password_hash)

    if user is None or not password_ok:
        raise AuthenticationError("Incorrect username or password")

    return _start_session(response, user.username)


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"status": "logged_out"}


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: str = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse(username=current_user)
