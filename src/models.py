"""Shared data models for the AI news agent pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class Article:
    """A single candidate news item pulled from an RSS feed."""

    id: str  # stable hash of the link, used as the dedupe/idempotency key
    title: str
    summary: str
    link: str
    published_at: datetime

    def to_prompt_line(self) -> str:
        return f"- {self.title}: {self.summary} ({self.link})"


@dataclass(slots=True)
class CuratedSelection:
    """Output of the Curator agent: which article was chosen, and why."""

    article: Article
    reason: str
    novelty_score: float  # 0.0 (very similar to recent posts) .. 1.0 (very novel)
    similar_past_titles: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GeneratedPost:
    """Output of the Writer agent: the publishable artifact."""

    title: str
    body_markdown: str
    mastodon_post: str
    source_article_id: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
