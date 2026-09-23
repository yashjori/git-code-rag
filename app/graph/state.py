"""Typed state passed between LangGraph RAG nodes."""

from __future__ import annotations

from typing import TypedDict

from app.retrieval.retriever import RetrievedDocument


class RAGState(TypedDict, total=False):
    question: str
    repository_id: str
    branch: str
    normalized_question: str
    retrieved_documents: list[RetrievedDocument]
    context: str
    answer: str
    sources: list[dict]
