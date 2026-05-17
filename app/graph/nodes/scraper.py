"""Scraper node — fetches RSS articles and persists new ones to DB."""
import logging

from app.database.repository import Repository
from app.graph.state import PipelineState
from app.scrapers.anthropic import AnthropicScraper

logger = logging.getLogger(__name__)


def scraper_node(state: PipelineState, repo: Repository) -> dict:
    scraper = AnthropicScraper()
    articles = scraper.get_articles(hours=state["hours"])
    article_dicts = [a.model_dump() for a in articles]
    inserted = repo.bulk_insert_anthropic_articles(article_dicts)

    pending = repo.get_articles_without_summary()
    logger.info(
        "Scraper: %d in feeds, %d inserted, %d pending summary",
        len(articles), inserted, len(pending),
    )
    return {"articles": pending}
