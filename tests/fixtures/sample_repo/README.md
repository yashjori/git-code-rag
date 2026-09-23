# Sample Service

A tiny fixture repository used by the git-code-assistant test suite to
exercise ingestion, chunking, and retrieval end to end.

## What's here

- `app/main.py`: FastAPI app entrypoint and health check.
- `app/auth/routes.py`: login/logout HTTP routes.
- `app/auth/service.py`: `authenticate_user`, credential checking, `UserService`.
- `app/auth/jwt.py`: `create_access_token` / `verify_access_token`.
- `app/database.py`: database connection configuration (`DATABASE_URL`) and
  a minimal in-memory `Connection`.

This is not a runnable production service; it exists to give the RAG
pipeline realistic, small source files to index.
