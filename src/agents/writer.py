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
            "You are an experienced journalist, blogger, and editor writing for a human audience.\n"
            "Your task is to transform the source article into a compelling, human-written blog post or daily briefing.\n\n"
            "Requirements:\n"
            "1. DO NOT write like an AI summarizer. Avoid generic phrases ('The article discusses', 'In conclusion').\n"
            "2. Write with a natural human voice. Sound thoughtful, curious, and conversational. Allow personality.\n"
            "3. Focus on WHY the story matters. Explain implications, trade-offs, and real-world relevance.\n"
            "4. Include specificity. Mention concrete examples from the source. Avoid vague philosophy.\n"
            "5. Create variation in sentence length and structure.\n"
            "6. Add a human-curated perspective: provide a brief interpretation ('What stood out to me').\n"
            "7. Do not sound overly formal or academic.\n\n"
            "Output Format (Markdown):\n"
            "# Headline\n"
            "## Why This Story Matters\n"
            "(2-3 engaging paragraphs)\n"
            "## Key Insight\n"
            "(Explain the central idea in a clear, human way)\n"
            "## Real-World Impact\n"
            "(Discuss practical implications)\n"
            "## Curator's Take\n"
            "(A short personal interpretation, observation, or thought-provoking question)\n\n"
            "The final result should feel like it was written by a thoughtful human editor.\n\n"
            "--- STORY TO COVER ---\n"
            f"Title: {article.title}\nSummary: {article.summary}\nSource: {article.link}\n"
            f"Why this story was chosen: {selection.reason}\n{context_note}\n\n"
            "--- INSTRUCTIONS ---\n"
            "Also write a separate short Mastodon post (max 500 characters, plain text) with relevant hashtags.\n\n"
            "Return ONLY valid JSON exactly like this example (do not wrap in markdown blocks like ```json):\n"
            '{"title": "Awesome Title", "body_markdown": "Full markdown text here", "mastodon_post": "Social post here"}'
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
