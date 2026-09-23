from fastapi import APIRouter, Depends

from app.api.dependencies import get_chat_service, get_current_user
from app.models.schemas import ChatQueryRequest, ChatQueryResponse, SourceReference
from app.services.chat_service import ChatService

# Gated behind login: each query is a paid Groq call plus a Qdrant search.
router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/query", response_model=ChatQueryResponse)
def query_repository(
    request: ChatQueryRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatQueryResponse:
    result = service.ask(request.repository_id, request.branch, request.question)
    return ChatQueryResponse(
        answer=result.answer,
        sources=[SourceReference(**source) for source in result.sources],
        repository_id=result.repository_id,
    )
