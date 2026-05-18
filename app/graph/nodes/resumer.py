"""Resumer node — single DB-read entry point for in-flight Articles.

Loads from the DB every Article still pending some downstream stage
(no summary yet, no Critic verdict yet, or approved-but-not-delivered)
and merges them into state["articles"]. Downstream Agents do not query
the DB for reads.
"""
import logging

from app.database.repository import Repository
from app.graph.state import PipelineState

logger = logging.getLogger(__name__)


def resumer_node(state: PipelineState, repo: Repository) -> dict:
    pending_summary = repo.get_articles_without_summary()
    pending_critic = repo.get_articles_pending_critic()
    pending_email = repo.get_articles_pending_email()
    pending_podcast = repo.get_articles_pending_podcast()

    # Dedupe by guid — categories overlap (an approved Article may be
    # pending both email and podcast)
    by_guid = {}
    for bucket in (pending_summary, pending_critic, pending_email, pending_podcast):
        for article in bucket:
            by_guid[article.guid] = article

    articles = list(by_guid.values())
    logger.info(
        "Resumer: %d unique articles (no-summary=%d, no-verdict=%d, "
        "approved-no-email=%d, approved-no-podcast=%d)",
        len(articles),
        len(pending_summary), len(pending_critic),
        len(pending_email), len(pending_podcast),
    )
    return {"articles": articles}
