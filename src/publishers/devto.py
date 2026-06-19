"""Publish to Dev.to: free, instant API key, no approval queue."""
from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

_DEVTO_URL = "https://dev.to/api/articles"


def publish_to_devto(api_key: str, title: str, body_markdown: str, tags: list[str] | None = None) -> str:
    """Publishes the article and returns its public URL."""
    payload = {
        "article": {
            "title": title,
            "body_markdown": body_markdown,
            "published": True,
            "tags": tags or ["ai", "news"],
        }
    }
    resp = requests.post(
        _DEVTO_URL,
        json=payload,
        headers={"api-key": api_key, "Content-Type": "application/json"},
        timeout=20,
    )
    resp.raise_for_status()
    url = resp.json()["url"]
    logger.info("Published to Dev.to: %s", url)
    return url
