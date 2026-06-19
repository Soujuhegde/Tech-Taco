"""Persistent vector memory of previously published posts.

This is what lets the Curator agent ask "have we basically covered this
story in the last 30 days?" instead of blindly picking the first headline.

Persistence note: ChromaDB's PersistentClient writes to a local directory
(`CHROMA_DB_PATH`). On a long-lived host (self-hosted n8n box, your laptop)
that directory just sits on disk between runs. On ephemeral CI runners
(GitHub Actions), the workflow in `.github/workflows/daily_run.yml` commits
that directory back to the repo after each run — a "git as a free database"
pattern that keeps this at $0 with no external hosted vector DB required.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Protocol

import chromadb

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "posts"


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class PostMemory:
    def __init__(self, path: str, embedder: Embedder) -> None:
        self._embedder = embedder
        self._client = chromadb.PersistentClient(path=path)
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_post(self, post_id: str, text: str, metadata: dict) -> None:
        """Store a published post's embedding so future runs can avoid repeats."""
        embedding = self._embedder.embed(text)
        meta = {**metadata, "timestamp": time.time()}
        self._collection.upsert(
            ids=[post_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[meta],
        )
        logger.info("Stored post in memory: %s", post_id)

    def query_similar(self, text: str, n_results: int = 3, window_days: int | None = None) -> list[dict]:
        """Return the most similar past posts, optionally restricted to a time window.

        Returns a list of {id, document, metadata, distance}, sorted by
        distance ascending (0.0 = identical, larger = more different, since
        we configured the collection with cosine distance).
        """
        if self._collection.count() == 0:
            return []

        where = None
        if window_days is not None:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).timestamp()
            where = {"timestamp": {"$gte": cutoff}}

        try:
            result = self._collection.query(
                query_embeddings=[self._embedder.embed(text)],
                n_results=min(n_results, self._collection.count()),
                where=where,
            )
        except Exception:
            logger.exception("Similarity query failed; treating as no prior context.")
            return []

        matches = []
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]
        for i, doc, meta, dist in zip(ids, docs, metas, dists):
            matches.append({"id": i, "document": doc, "metadata": meta, "distance": dist})
        return matches

    def prune_old(self, days: int) -> None:
        """Delete entries older than the retention window to keep the store small."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()
        try:
            self._collection.delete(where={"timestamp": {"$lt": cutoff}})
        except Exception:
            logger.exception("Prune failed (non-fatal); memory will just grow this run.")

    def count(self) -> int:
        return self._collection.count()
