"""Tests for src.memory.vector_store.PostMemory.

Uses a deterministic FakeEmbedder (see conftest.py) so these tests never
call the real Gemini embeddings endpoint, and a tmp_path-backed Chroma
PersistentClient so each test gets a clean, isolated store on disk.
"""
from __future__ import annotations

import time as time_module

from src.memory import vector_store as vs_module
from src.memory.vector_store import PostMemory


def _make_memory(tmp_path, fake_embedder) -> PostMemory:
    return PostMemory(path=str(tmp_path / "chroma_db"), embedder=fake_embedder)


def test_query_similar_on_empty_store_returns_empty_list(tmp_path, fake_embedder):
    memory = _make_memory(tmp_path, fake_embedder)
    assert memory.query_similar("anything") == []


def test_add_and_query_similar_finds_closest_match(tmp_path, fake_embedder):
    memory = _make_memory(tmp_path, fake_embedder)
    memory.add_post("post-1", "OpenAI releases a new model", {"title": "Post 1"})
    memory.add_post("post-2", "A completely unrelated story about cheese", {"title": "Post 2"})

    matches = memory.query_similar("OpenAI releases a new model", n_results=1)

    assert len(matches) == 1
    assert matches[0]["id"] == "post-1"
    assert matches[0]["distance"] < 0.01  # identical text -> identical fake embedding -> ~0 distance


def test_window_days_excludes_old_entries(tmp_path, fake_embedder, monkeypatch):
    memory = _make_memory(tmp_path, fake_embedder)

    # Add an "old" post by faking time.time() during the add_post call.
    sixty_days_ago = time_module.time() - 60 * 24 * 60 * 60
    monkeypatch.setattr(vs_module.time, "time", lambda: sixty_days_ago)
    memory.add_post("old-post", "Old story about robots", {"title": "Old"})
    monkeypatch.undo()  # restore real time.time for the rest of the test

    memory.add_post("new-post", "Old story about robots", {"title": "New"})  # same text on purpose

    matches = memory.query_similar("Old story about robots", n_results=5, window_days=30)

    ids = {m["id"] for m in matches}
    assert "new-post" in ids
    assert "old-post" not in ids


def test_prune_old_removes_entries_past_the_window(tmp_path, fake_embedder, monkeypatch):
    memory = _make_memory(tmp_path, fake_embedder)

    sixty_days_ago = time_module.time() - 60 * 24 * 60 * 60
    monkeypatch.setattr(vs_module.time, "time", lambda: sixty_days_ago)
    memory.add_post("old-post", "Stale content", {"title": "Old"})
    monkeypatch.undo()

    memory.add_post("new-post", "Fresh content", {"title": "New"})
    assert memory.count() == 2

    memory.prune_old(days=30)

    assert memory.count() == 1
