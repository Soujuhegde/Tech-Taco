"""Orchestrator: fetch -> curate (LangGraph) -> write (LangGraph) -> publish -> remember.

Run directly:
    python main.py

Scheduled for free via .github/workflows/daily_run.yml (GitHub Actions cron).
"""
from __future__ import annotations

import logging

from openai import OpenAI

from src.agents.curator import CuratorAgent
from src.agents.graph import build_graph
from src.agents.writer import WriterAgent
from src.config import get_settings
from src.fetchers.news_fetcher import fetch_candidate_articles
from src.memory.embeddings import LocalEmbedder
from src.memory.vector_store import PostMemory
from src.publishers.devto import publish_to_devto
from src.publishers.mastodon import publish_to_mastodon
from src.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


def run() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    # Initialize Sarvam API client (using OpenAI compatible interface)
    client = OpenAI(
        base_url="https://api.sarvam.ai/v1",
        api_key=settings.sarvam_api_key
    )
    
    # Initialize LocalEmbedder for ChromaDB
    embedder = LocalEmbedder(model_name=settings.local_embedding_model)
    memory = PostMemory(path=settings.chroma_db_path, embedder=embedder)

    # 1. Fetch
    candidates = fetch_candidate_articles(
        feed_urls=settings.rss_feed_list,
        lookback_hours=settings.lookback_hours,
        max_articles=settings.max_candidates,
    )
    if not candidates:
        logger.info("No new AI articles in the lookback window. Exiting cleanly.")
        return

    # 2 & 3. Curate + Write (LangGraph pipeline)
    curator = CuratorAgent(
        client=client,
        memory=memory,
        model=settings.sarvam_chat_model,
        top_k=settings.curator_top_k,
        memory_window_days=settings.memory_window_days,
    )
    writer = WriterAgent(client=client, model=settings.sarvam_chat_model)
    graph = build_graph(curator, writer)

    result = graph.invoke({"candidates": candidates})

    if result.get("error") or not result.get("post"):
        logger.error("Pipeline did not produce a post: %s", result.get("error"))
        return

    selection = result["selected"]
    post = result["post"]
    logger.info(
        "Curator picked '%s' (novelty=%.2f). Reason: %s",
        selection.article.title,
        selection.novelty_score,
        selection.reason,
    )

    if settings.dry_run:
        logger.info("DRY_RUN enabled — generated post:\n%s", post)
        return

    # 4. Publish (each platform fails independently)
    article_url: str | None = None
    try:
        article_url = publish_to_devto(settings.devto_api_key, post.title, post.body_markdown)
    except Exception:
        logger.exception("Dev.to publish failed.")

    if article_url:
        try:
            publish_to_mastodon(
                api_base_url=settings.mastodon_api_base_url,
                access_token=settings.mastodon_access_token,
                post_text=f"{post.mastodon_post}\n\n{article_url}",
            )
        except Exception:
            logger.exception("Mastodon publish failed (blog post is still live).")
    else:
        logger.warning("Skipping Mastodon post since there's no article URL to share.")

    # 5. Remember (so tomorrow's Curator knows this topic was just covered)
    try:
        memory.add_post(
            post_id=post.source_article_id,
            text=f"{post.title}. {post.body_markdown[:500]}",
            metadata={"title": post.title, "url": article_url or ""},
        )
        memory.prune_old(days=settings.memory_window_days)
    except Exception:
        logger.exception("Failed to write to memory (non-fatal; tomorrow's run still works).")


if __name__ == "__main__":
    run()
