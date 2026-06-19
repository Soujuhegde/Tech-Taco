"""Local embeddings using sentence-transformers.

Kept separate from vector_store.py so it's trivial to mock in tests and
swap out.
"""
from __future__ import annotations

import logging

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class LocalEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        logger.info("Loading local embedding model: %s", model_name)
        self._model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        embedding = self._model.encode(text)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self._model.encode(texts)
        return [emb.tolist() for emb in embeddings]
