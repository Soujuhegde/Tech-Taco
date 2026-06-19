"""Wires the Curator -> Writer pipeline into a compiled LangGraph graph.

START -> curator -> (writer | END) -> END

The conditional edge after the curator means a curation failure (e.g. no
candidates, or the judge call errored out after retries) short-circuits
straight to END instead of calling the Writer on an empty selection.
"""
from __future__ import annotations

from typing import Protocol

from langgraph.graph import END, StateGraph

from src.agents.state import AgentState


class GraphNode(Protocol):
    def run(self, state: AgentState) -> AgentState: ...


def _route_after_curator(state: AgentState) -> str:
    if state.get("error") or not state.get("selected"):
        return "end"
    return "writer"


def build_graph(curator_agent: GraphNode, writer_agent: GraphNode):
    graph = StateGraph(AgentState)
    graph.add_node("curator", curator_agent.run)
    graph.add_node("writer", writer_agent.run)

    graph.set_entry_point("curator")
    graph.add_conditional_edges(
        "curator",
        _route_after_curator,
        {"writer": "writer", "end": END},
    )
    graph.add_edge("writer", END)

    return graph.compile()
