"""Writer agent.

Takes the Curator's single chosen story (plus its reasoning and any
nearby-but-not-too-similar past posts) and drafts the publishable content.
Passing the "similar past posts" context to the writer — even when the
story was still chosen — lets it explicitly take a different angle instead
of accidentally rehashing a post from two weeks ago.
"""
from __future__ import annotations

import json
import logging
import re

from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.agents.state import AgentState
from src.models import GeneratedPost

logger = logging.getLogger(__name__)


class WriterAgent:
    def __init__(self, client: OpenAI, model: str = "sarvam-m") -> None:
        self._client = client
        self._model = model

    def run(self, state: AgentState) -> AgentState:
        selection = state.get("selected")
        if selection is None or state.get("error"):
            return state  # nothing to write; upstream error already recorded

        try:
            post = self._draft(selection)
            return {**state, "post": post}
        except Exception as exc:  # noqa: BLE001
            logger.exception("Writer agent failed.")
            return {**state, "error": f"Writer failed: {exc}"}

    @retry(
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(4),
        retry=retry_if_exception_type(Exception),
    )
    def _draft(self, selection) -> GeneratedPost:
        article = selection.article
        context_note = (
            f"Note: these related posts ran recently, so take a distinct angle: "
            f"{', '.join(selection.similar_past_titles)}."
            if selection.similar_past_titles
            else "No closely related posts have run recently — feel free to cover it directly."
        )

        prompt = (
            "You are an AI news writer. Write a ~400-word blog post in markdown "
            "with an engaging title, covering this story:\n\n"
            f"Title: {article.title}\nSummary: {article.summary}\nSource: {article.link}\n\n"
            f"Why this story was chosen: {selection.reason}\n{context_note}\n\n"
            "Also write a separate short Mastodon post or thread (max 500 characters, plain text, no "
            "markdown) with relevant hashtags.\n\n"
            'Return ONLY valid JSON exactly like this example:\n'
            '{"title": "Awesome Title", "body_markdown": "Full text here", "mastodon_post": "Social post here"}'
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2500,
        )

        msg = response.choices[0].message
        content = msg.content or msg.reasoning_content
        if not content:
            raise ValueError("Writer received empty response from API.")
            
        # Robust JSON extraction
        start_idx = content.find('{')
        if start_idx == -1:
            raise ValueError(f"Could not extract JSON from writer response: {content}")
            
        data = None
        for end_idx in range(len(content), start_idx, -1):
            if content[end_idx-1] == '}':
                try:
                    data = json.loads(content[start_idx:end_idx])
                    break
                except (json.JSONDecodeError, TypeError):
                    continue
                    
        if data is None:
            logger.error("Writer got non-JSON output: %s", content)
            raise ValueError("Could not parse Writer's response")

        for key in ("title", "body_markdown", "mastodon_post"):
            if key not in data or not data[key]:
                raise ValueError(f"Writer response missing/empty key: {key}")

        return GeneratedPost(
            title=data["title"],
            body_markdown=data["body_markdown"],
            mastodon_post=data["mastodon_post"],
            source_article_id=article.id,
        )
