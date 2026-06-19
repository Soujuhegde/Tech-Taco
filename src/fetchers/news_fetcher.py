"""Fetch and dedupe recent AI news from free RSS feeds.

No API key, no quota, no ToS restriction on production use — unlike
NewsAPI.org's free "developer" plan, which explicitly forbids this.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone

import feedparser

from src.models import Article

logger = logging.getLogger(__name__)


def _make_id(link: str) -> str:
    """Stable, short, deterministic id used as the dedupe/idempotency key."""
    return hashlib.sha256(link.encode("utf-8")).hexdigest()[:16]


def _parse_published(entry) -> datetime | None:
    struct_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if not struct_time:
        return None
    return datetime(*struct_time[:6], tzinfo=timezone.utc)


def fetch_candidate_articles(
    feed_urls: list[str],
    lookback_hours: int = 24,
    max_articles: int = 8,
) -> list[Article]:
    """Pull recent entries from each feed, dedupe by link, sort newest-first.

    A single bad/unreachable feed never aborts the whole run — it's logged
    and skipped, since RSS feeds occasionally go down or change shape.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    seen_links: set[str] = set()
    articles: list[Article] = []

    for feed_url in feed_urls:
        try:
            parsed = feedparser.parse(feed_url)
            if parsed.bozo and not parsed.entries:
                logger.warning("Feed unreachable or malformed, skipping: %s", feed_url)
                continue

            for entry in parsed.entries:
                link = entry.get("link")
                title = (entry.get("title") or "").strip()
                if not link or not title or link in seen_links:
                    continue

                published_at = _parse_published(entry) or datetime.now(timezone.utc)
                if published_at < cutoff:
                    continue

                seen_links.add(link)
                summary = (entry.get("summary") or entry.get("description") or "")[:500]
                articles.append(
                    Article(
                        id=_make_id(link),
                        title=title,
                        summary=summary,
                        link=link,
                        published_at=published_at,
                    )
                )
        except Exception:  # noqa: BLE001 - one feed's failure must not kill the run
            logger.exception("Failed to fetch/parse feed: %s", feed_url)
            continue

    articles.sort(key=lambda a: a.published_at, reverse=True)
    logger.info("Fetched %d candidate articles from %d feeds.", len(articles), len(feed_urls))
    return articles[:max_articles]
