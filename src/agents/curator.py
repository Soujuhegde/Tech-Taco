"""Curator agent.

Two-stage selection, deliberately not "ask the LLM to pick one of 8 things"
in a single shot:

  1. Cheap, deterministic stage: embed every candidate and compare it
     against the last `memory_window_days` of published posts in ChromaDB.
     This produces a novelty score per candidate with zero extra LLM calls.
  2. One LLM call, scoped to only the top-K most novel candidates, to
     make the final "most newsworthy" judgment call with a written reason.
"""
from __future__ import annotations

import json
import logging
import re

from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.agents.state import AgentState
from src.memory.vector_store import PostMemory
from src.models import Article, CuratedSelection

logger = logging.getLogger(__name__)


class CuratorAgent:
    def __init__(
        self,
        client: OpenAI,
        memory: PostMemory,
        model: str = "sarvam-m",
        top_k: int = 3,
        memory_window_days: int = 30,
    ) -> None:
        self._client = client
        self._memory = memory
        self._model = model
        self._top_k = top_k
        self._memory_window_days = memory_window_days

    def run(self, state: AgentState) -> AgentState:
        candidates: list[Article] = state.get("candidates", [])
        if not candidates:
            return {**state, "error": "No candidate articles to curate."}

        try:
            scored = self._score_novelty(candidates)
            shortlist = sorted(scored, key=lambda s: s[1], reverse=True)[: self._top_k]
            selection = self._judge(shortlist)
            return {**state, "selected": selection, "error": None}
        except Exception as exc:  # noqa: BLE001
            logger.exception("Curator agent failed.")
            return {**state, "error": f"Curator failed: {exc}"}

    def _score_novelty(self, candidates: list[Article]) -> list[tuple[Article, float, list[str]]]:
        """Returns (article, novelty_score, nearest_past_titles) for each candidate."""
        scored = []
        for article in candidates:
            text = f"{article.title}. {article.summary}"
            matches = self._memory.query_similar(
                text, n_results=2, window_days=self._memory_window_days
            )
            if not matches:
                novelty = 1.0  # nothing in memory yet (or genuinely novel) -> max novelty
                nearest_titles = []
            else:
                novelty = max(0.0, min(1.0, matches[0]["distance"]))
                nearest_titles = [m["metadata"].get("title", "") for m in matches]
            scored.append((article, novelty, nearest_titles))
        return scored

    @retry(
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(4),
        retry=retry_if_exception_type(Exception),
    )
    def _judge(self, shortlist: list[tuple[Article, float, list[str]]]) -> CuratedSelection:
        options_text = "\n".join(
            f"{i}. \"{article.title}\" — {article.summary}\n"
            f"   novelty_score={novelty:.2f} (1.0 = nothing similar posted recently)\n"
            f"   nearest_past_posts={nearest_titles or 'none'}"
            for i, (article, novelty, nearest_titles) in enumerate(shortlist)
        )
        prompt = (
            "You are an AI news editor choosing ONE story for today's blog post. "
            "Pick the option that is both genuinely newsworthy AND most novel "
            "relative to what's already been covered recently (higher novelty_score "
            "is better, but don't pick a trivial story just because it scores high).\n\n"
            f"{options_text}\n\n"
            'Return ONLY valid JSON exactly like this example:\n'
            '{"selected_index": 0, "reason": "Your one sentence reason here."}'
        )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "You are an expert AI news editor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1500,
        )
        
        msg = response.choices[0].message
        content = msg.content or msg.reasoning_content
        if not content or not content.strip():
            logger.error(f"Empty content from Sarvam API. Raw response: {response}")
            raise ValueError("Empty or None response from API.")
        
        text = content.strip()
        
        start_idx = text.find('{')
        if start_idx == -1:
            logger.error(f"Raw response contained no JSON object: {text}")
            raise ValueError("Could not find JSON object in response")
            
        data = None
        # Try to parse the largest possible valid JSON block starting from the first '{'
        for end_idx in range(len(text), start_idx, -1):
            if text[end_idx-1] == '}':
                try:
                    data = json.loads(text[start_idx:end_idx])
                    break
                except json.JSONDecodeError:
                    continue
                    
        if data is None:
            logger.error(f"Failed to parse any valid JSON from: {text}")
            raise ValueError("Could not extract valid JSON from response")
        
        idx = int(data["selected_index"])
        if not (0 <= idx < len(shortlist)):
            raise ValueError(f"Judge returned out-of-range index: {idx}")

        article, novelty, nearest_titles = shortlist[idx]
        return CuratedSelection(
            article=article,
            reason=data.get("reason", ""),
            novelty_score=novelty,
            similar_past_titles=nearest_titles,
        )
