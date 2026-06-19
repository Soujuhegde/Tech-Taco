"""LangGraph state shared between the Curator and Writer nodes."""
from __future__ import annotations

from typing import TypedDict

from src.models import Article, CuratedSelection, GeneratedPost


class AgentState(TypedDict, total=False):
    candidates: list[Article]
    selected: CuratedSelection | None
    post: GeneratedPost | None
    error: str | None
