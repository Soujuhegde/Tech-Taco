"""Tests for src.fetchers.news_fetcher.

feedparser.parse is monkeypatched so these tests run offline and instantly,
covering: cross-feed dedupe by link, recency cutoff, max_articles cap, and
graceful handling of one feed being broken.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pytest

from src.fetchers import news_fetcher


class _FakeParsed:
    def __init__(self, entries: list[dict], bozo: bool = False) -> None:
        self.entries = entries
        self.bozo = bozo
        self.bozo_exception = "fake error" if bozo else None


def _struct_time(dt: datetime) -> time.struct_time:
    return dt.utctimetuple()


def _entry(title: str, link: str, age_hours: float) -> dict:
    published = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    return {
        "title": title,
        "summary": f"Summary for {title}",
        "link": link,
        "published_parsed": _struct_time(published),
    }


@pytest.fixture
def patched_feeds(monkeypatch):
    feed_a = "https://example.com/feed-a.xml"
    feed_b = "https://example.com/feed-b.xml"
    feed_broken = "https://example.com/feed-broken.xml"

    parsed_by_url = {
        feed_a: _FakeParsed(
            [
                _entry("Recent story 1", "https://news.example/1", age_hours=1),
                _entry("Duplicate story", "https://news.example/2", age_hours=2),
                _entry("Too old story", "https://news.example/3", age_hours=48),
            ]
        ),
        feed_b: _FakeParsed(
            [
                _entry("Duplicate story", "https://news.example/2", age_hours=2),  # same link as feed_a
                _entry("Recent story 2", "https://news.example/4", age_hours=3),
            ]
        ),
        feed_broken: _FakeParsed([], bozo=True),
    }

    def fake_parse(url: str):
        return parsed_by_url[url]

    monkeypatch.setattr(news_fetcher.feedparser, "parse", fake_parse)
    return [feed_a, feed_b, feed_broken]


def test_dedupes_across_feeds_and_filters_by_recency(patched_feeds):
    articles = news_fetcher.fetch_candidate_articles(
        feed_urls=patched_feeds, lookback_hours=24, max_articles=10
    )

    links = {a.link for a in articles}
    assert links == {"https://news.example/1", "https://news.example/2", "https://news.example/4"}
    assert "https://news.example/3" not in links  # too old, filtered out


def test_respects_max_articles_cap(patched_feeds):
    articles = news_fetcher.fetch_candidate_articles(
        feed_urls=patched_feeds, lookback_hours=24, max_articles=2
    )
    assert len(articles) == 2


def test_broken_feed_does_not_raise(patched_feeds):
    # feed_broken is already in patched_feeds; the call above already proves
    # it doesn't raise, but assert explicitly with only the broken feed too.
    articles = news_fetcher.fetch_candidate_articles(
        feed_urls=[patched_feeds[2]], lookback_hours=24, max_articles=10
    )
    assert articles == []


def test_sorted_newest_first(patched_feeds):
    articles = news_fetcher.fetch_candidate_articles(
        feed_urls=patched_feeds, lookback_hours=24, max_articles=10
    )
    timestamps = [a.published_at for a in articles]
    assert timestamps == sorted(timestamps, reverse=True)
