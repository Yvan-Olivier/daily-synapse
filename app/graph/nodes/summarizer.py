"""Summarizer node — generates structured summaries via Ollama."""
import logging

from app.database.repository import Repository
from app.graph.state import PipelineState
from app.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


def summarizer_node(state: PipelineState, repo: Repository) -> dict:
    llm = OllamaClient()
    articles = state["articles"]
    summarized = []
    errors = []

    for article in articles:
        content = article.description or article.title
        result = llm.summarize(title=article.title, content=content)

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
