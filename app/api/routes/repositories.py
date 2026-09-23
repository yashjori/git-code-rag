from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_repository_service
from app.models.repository import RepositoryRecord
from app.models.schemas import (
    DeleteRepositoryResponse,
    IndexRepositoryRequest,
    IndexRepositoryResponse,
    RepositoryListResponse,
    RepositoryStatusResponse,
)
from app.services.repository_service import RepositoryService

# Every route in this router requires a valid session - this is exactly the
# surface (repo indexing, which triggers paid Qdrant/Groq calls) that
# needs to be behind login, not left open to the internet.
router = APIRouter(dependencies=[Depends(get_current_user)])


def _to_status_response(record: RepositoryRecord) -> RepositoryStatusResponse:
    return RepositoryStatusResponse(
        repository_id=record.repository_id,
        provider=record.provider,
        repository_url=record.repository_url,
        branch=record.branch,
        indexed_at=record.indexed_at,
        files_indexed=record.files_indexed,
        chunks_created=record.chunks_created,
        status=record.status,
    )


@router.post("/index", response_model=IndexRepositoryResponse)
def index_repository(
    request: IndexRepositoryRequest,
    service: RepositoryService = Depends(get_repository_service),
) -> IndexRepositoryResponse:
    result = service.index_repository(
        request.provider, request.repository_url, request.branch, request.access_token
    )
    return IndexRepositoryResponse(
        repository_id=result.repository_id,
        status=result.status,
        files_scanned=result.files_scanned,
        files_indexed=result.files_indexed,
        chunks_created=result.chunks_created,
        branch=result.branch,
    )


@router.get("", response_model=RepositoryListResponse)
def list_repositories(
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryListResponse:
    records = service.list_repositories()
    return RepositoryListResponse(repositories=[_to_status_response(r) for r in records])


@router.get("/{repository_id}", response_model=RepositoryStatusResponse)
def get_repository_status(
    repository_id: str,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryStatusResponse:
    record = service.get_status(repository_id)
    return _to_status_response(record)


@router.delete("/{repository_id}", response_model=DeleteRepositoryResponse)
def delete_repository(
    repository_id: str,
    service: RepositoryService = Depends(get_repository_service),
) -> DeleteRepositoryResponse:
    service.delete_repository(repository_id)
    return DeleteRepositoryResponse(repository_id=repository_id, status="deleted")
