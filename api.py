from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

app = FastAPI(title="AI News Agent API")

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev only. Change in prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunResponse(BaseModel):
    status: str
    message: str
    post: dict | None = None
    reason: str | None = None
    error: str | None = None

@app.post("/api/run-agent", response_model=RunResponse)
def run_agent(background_tasks: BackgroundTasks):
    settings = get_settings()
    setup_logging(settings.log_level)

    client = OpenAI(
        base_url="https://api.sarvam.ai/v1",
        api_key=settings.sarvam_api_key
    )
    
    embedder = LocalEmbedder(model_name=settings.local_embedding_model)
    memory = PostMemory(path=settings.chroma_db_path, embedder=embedder)

    candidates = fetch_candidate_articles(
        feed_urls=settings.rss_feed_list,
        lookback_hours=settings.lookback_hours,
        max_articles=settings.max_candidates,
    )
    if not candidates:
        return RunResponse(status="success", message="No new AI articles in the lookback window.")

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
        return RunResponse(status="error", message="Pipeline failed", error=str(result.get("error")))

    selection = result["selected"]
    post = result["post"]
    
    # Normally we publish, but for the UI we'll just return the post 
    # and maybe publish in background if not dry_run
    if not settings.dry_run:
        background_tasks.add_task(publish_post, settings, post, memory)

    return RunResponse(
        status="success",
        message="Post generated successfully!",
        post={
            "title": post.title,
            "body_markdown": post.body_markdown,
            "mastodon_post": post.mastodon_post,
            "source_article_url": selection.article.link
        },
        reason=selection.reason
    )

def publish_post(settings, post, memory):
    try:
        article_url = publish_to_devto(settings.devto_api_key, post.title, post.body_markdown)
        if article_url:
            publish_to_mastodon(
                api_base_url=settings.mastodon_api_base_url,
                access_token=settings.mastodon_access_token,
                post_text=f"{post.mastodon_post}\n\n{article_url}",
            )
        memory.add_post(
            post_id=post.source_article_id,
            text=f"{post.title}. {post.body_markdown[:500]}",
            metadata={"title": post.title, "url": article_url or ""},
        )
        memory.prune_old(days=settings.memory_window_days)
    except Exception as e:
        logger.error(f"Background publish failed: {e}")
