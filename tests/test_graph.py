"""Tests for src.agents.graph.build_graph.

Uses stub Curator/Writer agents (no real Gemini calls) to verify the graph
*routes* correctly: the Writer should run after a successful curation, and
should be skipped entirely when curation fails.
"""
from __future__ import annotations

from src.agents.graph import build_graph


class _StubCurator:
    def __init__(self, result_state: dict) -> None:
        self._result_state = result_state
        self.called = False

    def run(self, state: dict) -> dict:
        self.called = True
        return {**state, **self._result_state}


class _StubWriter:
    def __init__(self) -> None:
        self.called = False

    def run(self, state: dict) -> dict:
        self.called = True
        return {**state, "post": "WRITER_RAN"}


def test_writer_runs_when_curator_succeeds():
    curator = _StubCurator({"selected": "some-article", "error": None})
    writer = _StubWriter()
    graph = build_graph(curator, writer)

    result = graph.invoke({"candidates": ["a", "b"]})

    assert curator.called is True
    assert writer.called is True
    assert result["post"] == "WRITER_RAN"


def test_writer_is_skipped_when_curator_fails():
    curator = _StubCurator({"selected": None, "error": "no candidates"})
    writer = _StubWriter()
    graph = build_graph(curator, writer)

    result = graph.invoke({"candidates": []})

    assert curator.called is True
    assert writer.called is False
    assert result.get("error") == "no candidates"
    assert "post" not in result
