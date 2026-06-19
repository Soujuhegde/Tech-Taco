"""Centralized configuration. Loads from environment variables / .env.

Using pydantic-settings gives us validation (fail fast on missing keys)
instead of discovering a typo'd env var name at 2am via a silent KeyError.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Sarvam ---
    sarvam_api_key: str = Field(..., alias="SARVAM_API_KEY")
    sarvam_chat_model: str = Field("sarvam-30b", alias="SARVAM_CHAT_MODEL")
    # For local embeddings using sentence-transformers
    local_embedding_model: str = Field("all-MiniLM-L6-v2", alias="LOCAL_EMBEDDING_MODEL")

    # --- News sources ---
    rss_feeds: str = Field(
        "https://techcrunch.com/category/artificial-intelligence/feed/,"
        "https://www.technologyreview.com/feed/,"
        "https://blog.google/technology/ai/rss/",
        alias="RSS_FEEDS",
    )
    lookback_hours: int = Field(24, alias="LOOKBACK_HOURS")
    max_candidates: int = Field(8, alias="MAX_CANDIDATES")

    # --- Memory / vector store ---
    chroma_db_path: str = Field("./data/chroma_db", alias="CHROMA_DB_PATH")
    memory_window_days: int = Field(30, alias="MEMORY_WINDOW_DAYS")
    curator_top_k: int = Field(3, alias="CURATOR_TOP_K")  # candidates the Gemini judge sees

    # --- Dev.to ---
    devto_api_key: str = Field("", alias="DEVTO_API_KEY")

    # --- Mastodon ---
    mastodon_api_base_url: str = Field("https://mastodon.social", alias="MASTODON_API_BASE_URL")
    mastodon_access_token: str = Field("", alias="MASTODON_ACCESS_TOKEN")

    # --- Runtime ---
    dry_run: bool = Field(False, alias="DRY_RUN")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    @property
    def rss_feed_list(self) -> list[str]:
        return [f.strip() for f in self.rss_feeds.split(",") if f.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so we parse/validate the environment exactly once per run."""
    return Settings()  # type: ignore[call-arg]  # values come from env/.env
