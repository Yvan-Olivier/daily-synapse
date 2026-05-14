"""Ollama LLM client — local, zero-cost inference for M0.

Uses Ollama's structured-output support (`format=` parameter) with a
Pydantic JSON schema to guarantee parseable responses.

In later milestones, this client will be replaced (or coexist) with
Claude Haiku / Sonnet through a common interface.
"""
import logging
import os
from typing import Optional

from ollama import Client
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SummaryOutput(BaseModel):
    """Structured response expected from the LLM."""
    title: str
    summary: str


SUMMARIZE_SYSTEM_PROMPT = """You are an expert tech and AI news summarizer.

Given an article from Anthropic (an AI safety / research company), produce:
- A short, punchy title (5 to 10 words) capturing the essence
- A 2-3 sentence summary highlighting the key points and why they matter

Be concise, technical, and avoid marketing fluff.
Output strictly valid JSON matching the requested schema."""


class OllamaClient:
    def __init__(
        self,
        model: Optional[str] = None,
        host: Optional[str] = None,
    ):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.client = Client(host=self.host)

    def summarize(self, title: str, content: str) -> Optional[SummaryOutput]:
        """Generate a structured summary for one article.

        Returns None if the LLM call fails or the response can't be parsed.
        """
        # Truncate to a reasonable context size for a 7B model
        snippet = (content or title)[:6000]
        user_prompt = (
            f"Article title: {title}\n\n"
            f"Article content / description:\n{snippet}"
        )

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SUMMARIZE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                format=SummaryOutput.model_json_schema(),
                options={"temperature": 0.3},
                think=False,
            )
            return SummaryOutput.model_validate_json(
                response.message.content
            )
        except Exception as exc:
            logger.error(
                "Ollama summarization failed for '%s': %s", title[:60], exc
            )
            return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = OllamaClient()
    result = client.summarize(
        title="Introducing Claude 3.5 Sonnet",
        content=(
            "We are excited to announce Claude 3.5 Sonnet, our most "
            "intelligent model yet. It outperforms competitors across a "
            "wide range of benchmarks, including graduate-level reasoning "
            "and undergraduate-level knowledge."
        ),
    )
    print(result)
