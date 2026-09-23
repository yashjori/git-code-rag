"""Groq LLM factory.

The only place ChatGroq is constructed. Model name and API key always come
from configuration - never hardcoded, never a literal string anywhere else
in the codebase.
"""

from __future__ import annotations

from langchain_groq import ChatGroq

# Deterministic, close-to-zero temperature is appropriate for codebase Q&A:
# we want the same evidence to produce the same grounded answer, not
# creative variation.
_GENERATION_TEMPERATURE = 0


def create_groq_llm(*, api_key: str, model: str) -> ChatGroq:
    if not api_key or not model:
        raise ValueError("GROQ_API_KEY and GROQ_MODEL must both be set")
    return ChatGroq(model_name=model, api_key=api_key, temperature=_GENERATION_TEMPERATURE)
