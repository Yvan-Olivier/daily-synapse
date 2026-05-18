"""Summarizer node — generates structured summaries via Ollama."""
import logging
from typing import Optional

from pydantic import BaseModel

from app.database.repository import Repository
from app.graph.state import PipelineState
from app.llm.base import OllamaBase

logger = logging.getLogger(__name__)

SUMMARIZE_SYSTEM_PROMPT = """You are an expert tech and AI news summarizer.

Given an AI or technology article, produce:
- A short, punchy title (5 to 10 words) capturing the essence
- A 2-3 sentence summary highlighting the key points and why they matter

Be concise, technical, and avoid marketing fluff.
Output strictly valid JSON matching the requested schema."""


class SummaryOutput(BaseModel):
    title: str
    summary: str


class SummarizerAgent(OllamaBase):
    def summarize(self, title: str, content: str) -> Optional[SummaryOutput]:
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
            return SummaryOutput.model_validate_json(response.message.content)
        except Exception as exc:
            logger.error("Ollama summarization failed for '%s': %s", title[:60], exc)
            return None


def summarizer_node(state: PipelineState, repo: Repository) -> dict:
    agent = SummarizerAgent()
    articles = state["articles"]
    summarized = []
    errors = []

    for article in articles:
        content = article.description or article.title
        result = agent.summarize(title=article.title, content=content)

        if result is None:
            errors.append(f"Summarizer failed for {article.guid}")
            logger.warning("Summarizer: FAILED for '%s'", article.title[:60])
            continue

        repo.update_summary(
            guid=article.guid,
            summary_title=result.title,
            summary=result.summary,
        )
        article.summary_title = result.title
        article.summary = result.summary
        summarized.append(article)
        logger.info("Summarizer: -> %s", result.title)

    logger.info("Summarizer: %d/%d succeeded", len(summarized), len(articles))
    return {"articles": summarized, "errors": errors}
