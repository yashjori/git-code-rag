"""Application entrypoint for the sample service."""

from fastapi import FastAPI

from app.auth.routes import router as auth_router

app = FastAPI(title="Sample Service")
app.include_router(auth_router, prefix="/auth")


@app.get("/health")
def health() -> dict[str, str]:
    """Basic liveness check used by the load balancer."""
    return {"status": "ok"}
