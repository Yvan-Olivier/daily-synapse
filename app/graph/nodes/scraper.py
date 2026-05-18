"""Scraper node — fetches RSS articles and persists new ones to DB.

Single responsibility: ingest fresh content. DB rehydration of in-flight
work from previous runs is the Resumer's job.
"""
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

    logger.info(
        "Scraper: %d in feeds, %d inserted (new)",
        len(articles), inserted,
    )
    return {}
