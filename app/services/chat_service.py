"""Chat query orchestration: builds and runs the compiled RAG graph."""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel

from app.core.exceptions import AppError, GraphExecutionError
from app.core.logging import get_logger
from app.graph.nodes import RAGNodes
from app.graph.rag_graph import build_rag_graph
from app.retrieval.retriever import CodeRetriever
from app.services.repository_service import RepositoryService

logger = get_logger(__name__)


@dataclass(frozen=True)
class ChatResult:
    answer: str
    sources: list[dict]
    repository_id: str


class ChatService:
    def __init__(
        self,
        repository_service: RepositoryService,
        retriever: CodeRetriever,
        llm: BaseChatModel,
    ) -> None:
        nodes = RAGNodes(
            retriever=retriever,
            llm=llm,
            validate_repository=repository_service.validate_repository_branch,
        )
        self._graph = build_rag_graph(nodes)

    def ask(self, repository_id: str, branch: str, question: str) -> ChatResult:
        try:
            result = self._graph.invoke(
                {"question": question, "repository_id": repository_id, "branch": branch}
            )
        except AppError:
            raise
        except Exception as exc:
            logger.exception("graph execution failure: repository_id=%s", repository_id)
            raise GraphExecutionError(
                "Failed to answer the question due to an internal error"
            ) from exc

        return ChatResult(
            answer=result["answer"],
            sources=result["sources"],
            repository_id=repository_id,
        )
