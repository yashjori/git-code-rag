# Git Repository Code Assistant

RAG-based code assistant for GitHub and Azure DevOps repositories. Built
from `GITHUB_AZURE_CODE_RAG_QDRANT_SPEC.md` (the original build spec is not
included in this repo; see project history for the source).

## Stack

- Python 3.12+, FastAPI, Pydantic v2, Uvicorn, managed with `uv`.
- LangChain 1.x / LangGraph 1.x / `langchain-groq` for orchestration.
- Groq for answer generation (model configured via `GROQ_MODEL`, never
  hardcoded).
- Qdrant Cloud for both vector storage and embedding generation (Cloud
  Inference). No local ML embedding model runs in this process.
- SQLite (stdlib `sqlite3`) for repository metadata. No ORM.
- Frontend: React 19 + TypeScript + Vite + Tailwind CSS v4, in `frontend/`,
  managed with `bun`. Static SPA, no SSR, no its own backend/API routes.

## Architectural decisions that diverge from a literal spec reading

The original spec had two internal contradictions. Both are resolved in
favor of Qdrant Cloud, since that's what the spec's title, majority of
sections, and acceptance criteria require:

1. **Embeddings are Qdrant Cloud Inference only.** A local HuggingFace
   `BAAI/bge-small-en-v1.5` embedding service was described in one section
   but explicitly forbidden in another. There is no `sentence-transformers`
   or `transformers` dependency in this repo, and there should not be one
   added later without a deliberate decision to change this.
2. **The vector store is Qdrant Cloud, not Chroma.** A single mention of
   "Chroma" in a deliverables list was a leftover from an earlier draft.

Two more decisions followed from researching the actual current Qdrant
Cloud Inference API (not assumed from older tutorials):

3. **`QDRANT_EMBEDDING_DIMENSION` is required configuration.** Qdrant
   Cloud Inference does not expose a model's vector size through the
   client API - it's only visible in the cluster's Inference tab in the
   Qdrant Cloud console. `QdrantVectorStoreService.ensure_collection()`
   needs this to create the collection correctly the first time.
4. **`app/vectorstore/qdrant_store.py` uses `qdrant_client` directly, not
   `langchain-qdrant`.** `langchain-qdrant`'s `QdrantVectorStore` expects a
   local `Embeddings` object that returns pre-computed vectors; it does not
   support Qdrant's server-side Cloud Inference (`models.Document(text=,
   model=)` passed straight into `upsert`/`query_points`). Wrapping the raw
   client ourselves still satisfies the spec's requirement to keep
   Qdrant-specific code behind one service.

If you're extending this project and considering switching either of these
back, re-read `README.md`'s "Deviations from the original spec" section
first.

Two decisions were made for the frontend (added after the backend was
already built and verified; the original spec explicitly excluded a
frontend from V1):

5. **Vite + React, not Next.js**, despite Next.js being the org-wide
   default frontend framework. This app has no SSR/SEO need and no
   multi-page routing depth that would justify it; it's a static SPA that
   calls the FastAPI backend directly. The session's own declared
   `Dev server port: 5173` (Vite's default, not Next's 3000) was the
   concrete signal that settled this.
6. **`GET /api/v1/repositories` (list all) was added to the backend.** Not
   in the original spec, added because a real "browse what's indexed" UI
   is impossible without it. Same layering as the existing endpoints:
   `RepositoryMetadataStore.list_all()` -> `RepositoryService.list_repositories()`
   -> the route.

The frontend has no login/auth screen, matching the backend, which has
none either (spec explicitly scoped auth out of V1). Don't add one to
just the frontend; that would be decorative, not real access control.

Two more decisions were made fixing a real gap found after the frontend
shipped: a single server-wide `GITHUB_TOKEN`/`AZURE_DEVOPS_PAT` doesn't
work once different people need access to different private repos:

7. **`IndexRepositoryRequest.access_token` (optional, per-request)
   overrides the server default for that one clone.** Not a user-account
   system, deliberately: the browser tab is already the per-user boundary
   without one. Threaded through `factory.create_provider(..., access_token=)`
   -> `GitHubProvider`/`AzureDevOpsProvider`. Never persisted (not in
   `RepositoryRecord`, not logged, not echoed in any response). The
   frontend remembers it per-provider in `sessionStorage` only
   (`frontend/src/hooks/useSessionToken.ts`), never `localStorage`.
8. **`app/repositories/git_auth.py`: tokens are injected via
   `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_0`/`GIT_CONFIG_VALUE_0` environment
   variables (a one-time `http.extraheader` override), not embedded in the
   clone URL.** Verified empirically (see the JSON conversation history if
   you need the exact repro) that `https://{token}@host/...` URLs get
   written by git into the cloned repo's `.git/config` in plaintext - a
   real problem once individual users' PATs start flowing through, not
   just a shared server secret. Also verified that `git clone -c
   key=value` is NOT equivalent (that literally means "set config inside
   the new repository" per git's own docs) - the env-var form is the
   correct one. Both `GitHubProvider` and `AzureDevOpsProvider` build their
   clone `env` via `build_auth_env()`, never a token-in-URL string, even
   for the `.env`-default token case.

If you touch `clone_repository()` in either provider, re-verify both
properties: the clone still works, and the cloned repo's `.git/config`
contains no credential.

## Layering

```text
app/repositories/   provider abstraction (GitHub, Azure DevOps) -> local Path
app/ingestion/       local only: scan -> filter -> load -> chunk -> Documents
app/embeddings/      names the configured Qdrant Cloud Inference model
app/vectorstore/     all raw qdrant_client calls live here, nowhere else
app/retrieval/       wraps vectorstore, returns LangChain Documents + scores
app/llm/             Groq factory + prompts (grounding rules, prompt-injection framing)
app/graph/           LangGraph state/nodes/compiled graph
app/services/        orchestration: RepositoryService, ChatService
app/api/             FastAPI routes + dependency wiring
```

Nothing above `app/repositories/` should import a provider-specific
module. Nothing in `app/ingestion/` should import `app/embeddings/` or
`app/vectorstore/` - it produces `Document` objects and stops there.

`RepositoryService` takes its vector store as a lazy factory
(`vector_store_provider: Callable[[], QdrantVectorStoreService]`), not a
constructed instance, so read-only operations (`get_status`,
`validate_repository_branch`) work even when Qdrant isn't configured yet.
Only `index_repository` and `delete_repository` actually need it.

## Testing

`uv run pytest`. The suite never calls Groq or Qdrant Cloud over the
network:

- `tests/unit/`: pure-function tests (URL parsing, filtering, language
  detection, chunk metadata, context formatting, source extraction, config
  validation).
- `tests/integration/test_ingestion_pipeline.py`: runs the real ingestion
  pipeline against `tests/fixtures/sample_repo/`, no network.
- `tests/integration/test_retrieval_and_graph.py`: exercises retrieval,
  repository isolation, and the full compiled LangGraph using an in-memory
  fake vector store and a fake LLM.
- `tests/integration/test_api.py`: FastAPI `TestClient` with
  `get_repository_service`/`get_chat_service` overridden by fakes.

Live verification against a real Qdrant Cloud cluster and Groq happens
outside the automated suite (manual curl / a throwaway script), since CI
should never require live third-party credentials.

## Known limitations (see README for the full list)

Symbol detection is regex-based (no Tree-sitter/AST in V1, per spec).
Re-indexing is full replacement, not incremental. No hybrid search,
reranking, conversation memory, or API-level auth. The frontend was
verified end-to-end in a real browser (chrome-devtools MCP: add/list/
select/query/delete flows, dark/light, mobile viewport, console/network
checks) rather than with an automated test suite - there is no
Vitest/Testing Library setup in `frontend/` yet.
