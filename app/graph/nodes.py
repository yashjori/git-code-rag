"""LangGraph RAG nodes.

Each node has one meaningful responsibility, per the spec's requirement
that LangGraph orchestrate real RAG steps rather than wrap a single LLM
call. Dependencies (retriever, LLM, repository validator) are injected so
this module never imports the vector store, Groq client, or database
directly - it only calls the abstractions it's given.
"""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.language_models import BaseChatModel

from app.core.exceptions import InvalidRequestError
from app.graph.formatting import extract_sources, format_context
from app.graph.state import RAGState
from app.llm.prompts import build_answer_messages, build_rewrite_messages
from app.retrieval.retriever import CodeRetriever

INSUFFICIENT_EVIDENCE_ANSWER = (
    "I could not find enough relevant code in the indexed repository to "
    "answer this confidently."
)


class RAGNodes:
    """Bound node functions sharing injected retriever/LLM/validator."""

    def __init__(
        self,
        *,
        retriever: CodeRetriever,
        llm: BaseChatModel,
        validate_repository: Callable[[str, str], None],
    ) -> None:
        self._retriever = retriever
        self._llm = llm
        self._validate_repository = validate_repository

    def validate_query(self, state: RAGState) -> dict:
        question = state["question"].strip()
        if not question:
            raise InvalidRequestError("question must not be empty")
        self._validate_repository(state["repository_id"], state["branch"])
        return {"question": question}

    def rewrite_query(self, state: RAGState) -> dict:
        messages = build_rewrite_messages(state["question"])
        response = self._llm.invoke(messages)
        rewritten = str(response.content).strip()
        return {"normalized_question": rewritten or state["question"]}

    def retrieve_code(self, state: RAGState) -> dict:
        retrieved = self._retriever.retrieve(
            state["normalized_question"],
            repository_id=state["repository_id"],
            branch=state["branch"],
        )
        return {"retrieved_documents": retrieved}

    def check_retrieval(self, state: RAGState) -> str:
        """Conditional-edge router, not a state-mutating node."""
        return "sufficient" if state["retrieved_documents"] else "insufficient"

    def build_context(self, state: RAGState) -> dict:
        return {"context": format_context(state["retrieved_documents"])}

    def generate_answer(self, state: RAGState) -> dict:
        messages = build_answer_messages(state["question"], state["context"])
        response = self._llm.invoke(messages)
        return {"answer": str(response.content)}

    def extract_sources_node(self, state: RAGState) -> dict:
        return {"sources": extract_sources(state["retrieved_documents"])}

    def fallback_response(self, state: RAGState) -> dict:
        return {"answer": INSUFFICIENT_EVIDENCE_ANSWER, "sources": []}
