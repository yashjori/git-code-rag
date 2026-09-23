"""HTTP routes for the login flow."""

from fastapi import APIRouter, HTTPException

from app.auth.service import AuthenticationError, authenticate_user

router = APIRouter()


@router.post("/login")
def login(username: str, password: str) -> dict:
    """Login endpoint: the entry point of the login flow.

    Delegates credential checking to authenticate_user and returns an
    access token on success, or a 401 on failure.
    """
    try:
        token = authenticate_user(username, password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
def logout() -> dict:
    """Logout endpoint. Stateless tokens mean this is a client-side no-op."""
    return {"status": "logged_out"}
