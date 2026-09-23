# Production backend image. Built and run directly on the target host
# (see deploy notes) - no cross-platform build concern.
FROM python:3.12-slim

# git is a runtime dependency, not just a build tool: GitPython shells out
# to the real `git` binary to clone repositories.
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY run.py ./

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
