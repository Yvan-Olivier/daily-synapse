"""Podcast script generator — Ollama local inference.

Takes a list of summarized articles and produces a 400-600 word
narrative monologue script for the daily podcast episode.
"""
import logging
from datetime import date
from typing import List, Optional

from app.database.models import AnthropicArticle
from app.llm.base import OllamaBase

logger = logging.getLogger(__name__)

SCRIPT_SYSTEM_PROMPT = """You are a professional tech podcast host writing a daily AI news briefing.

Your style: conversational yet sharp, narrative and flowing — not a bullet-point list read aloud.
Weave the stories together with natural transitions. Speak directly to the listener.

Structure (light, not rigid):
- Open with a one-sentence hook mentioning the date and number of stories
- Body: cover each story with context and why it matters, linking them where relevant
- Close with a short outro: "That's your Daily Synapse briefing for [date]. Stay curious."

Constraints:
- 400 to 600 words total
- English only
- No headers, no bullet points — pure flowing prose
- Do not mention "script" or "briefing notes" — write as if you are speaking"""


class ScriptWriter(OllamaBase):
    def write_script(
        self, articles: List[AnthropicArticle], episode_date: date
    ) -> Optional[str]:
        """Generate a podcast script from a list of summarized articles.

        Returns the script as a plain string, or None if generation fails.
        """
        date_str = episode_date.strftime("%B %d, %Y")
        n = len(articles)

        articles_block = "\n\n".join(
            f"Story {i}: {a.summary_title}\n{a.summary}"
            for i, a in enumerate(articles, 1)
        )

        user_prompt = (
            f"Today is {date_str}. You have {n} AI news {'story' if n == 1 else 'stories'} to cover.\n\n"
            f"{articles_block}\n\n"
            f"Write the podcast script now."
        )

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                options={"temperature": 0.7},
                think=False,
            )
            script = response.message.content.strip()
            word_count = len(script.split())
            logger.info("Script generated: %d words", word_count)
            return script
        except Exception as exc:
            logger.error("Script generation failed: %s", exc)
            return None
