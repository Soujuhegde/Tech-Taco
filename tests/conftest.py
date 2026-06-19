"""Shared pytest fixtures."""
from __future__ import annotations

import hashlib

import pytest


class FakeEmbedder:
    """Deterministic, dependency-free stand-in for GeminiEmbedder in tests.

    Maps text -> a small fixed-size vector derived from a hash, so identical
    text always yields an identical embedding (needed for similarity tests)
    without making any network calls.
    """

    DIM = 16

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [b / 255.0 for b in digest[: self.DIM]]


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()
