"""FastAPI application entrypoint.

Run with:

    uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.dependencies import get_user_store
from app.api.routes import auth, chat, health, repositories
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.models.user import UserRecord

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("%s starting up in %s mode", settings.app_name, settings.app_env)
    if not settings.is_groq_configured:
        logger.warning("GROQ_API_KEY/GROQ_MODEL not set - chat queries will fail")
    if not settings.is_qdrant_configured:
        logger.warning(
            "QDRANT_URL/QDRANT_EMBEDDING_MODEL/QDRANT_EMBEDDING_DIMENSION not set - "
            "indexing and retrieval will fail"
        )
    if not settings.is_auth_configured:
        logger.warning(
            "AUTH_SECRET_KEY is missing or too short (needs >=32 chars) - "
            "sessions cannot be issued or verified"
        )
    _ensure_bootstrap_admin()
    yield


def _ensure_bootstrap_admin() -> None:
    username = settings.bootstrap_admin_username
    password_hash = settings.bootstrap_admin_password_hash
    if not (username and password_hash):
        return
    store = get_user_store()
    if store.get(username) is None:
        store.create(
            UserRecord(
                username=username,
                password_hash=password_hash,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        logger.info("created bootstrap admin user '%s'", username)


app = FastAPI(
    title=settings.app_name,
    description=(
        "RAG-based code assistant that answers questions about indexed "
        "GitHub and Azure DevOps repositories using Qdrant Cloud and Groq."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
    # Sessions are a cookie now, not a header the frontend attaches itself -
    # cross-origin requests (local dev only; prod is same-origin) need this
    # for the cookie to actually be sent and accepted.
    allow_credentials=True,
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    logger.warning("request failed: %s", exc.message)
    return JSONResponse(status_code=exc.http_status, content={"detail": exc.message})


app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(
    repositories.router, prefix="/api/v1/repositories", tags=["repositories"]
)
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
