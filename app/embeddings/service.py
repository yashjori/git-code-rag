"""Embedding configuration for Qdrant Cloud Inference.

Embedding vectors are computed by Qdrant Cloud itself - the QdrantClient is
constructed with cloud_inference=True (see app/vectorstore/qdrant_store.py)
and text is sent as a qdrant_client.models.Document, not as a pre-computed
vector. No local HuggingFace/Sentence-Transformers model ever loads in this
process. This module is the single place that knows the configured model
name, so nothing else in the codebase hardcodes it.
"""

from __future__ import annotations

from qdrant_client import models


class EmbeddingService:
    """Wraps the Qdrant Cloud Inference model configured via env vars."""

    def __init__(self, model_name: str) -> None:
        if not model_name:
            raise ValueError("QDRANT_EMBEDDING_MODEL must be set")
        self.model_name = model_name

    def to_inference_document(self, text: str) -> models.Document:
        """Wrap text so Qdrant computes its embedding server-side on upsert
        or query, instead of any local embedding inference."""

        return models.Document(text=text, model=self.model_name)
