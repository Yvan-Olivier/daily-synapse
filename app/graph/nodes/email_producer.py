"""EmailProducer node — sends daily digest from curated articles in State."""
import logging

from app.database.repository import Repository
from app.email.sender import send_digest
from app.graph.state import PipelineState

logger = logging.getLogger(__name__)


def email_producer_node(state: PipelineState, repo: Repository) -> dict:
    articles = state["articles"]
    email_sent = send_digest(articles)

    if email_sent and articles:
        repo.mark_articles_emailed([a.guid for a in articles])
        logger.info("EmailProducer: sent digest with %d article(s)", len(articles))
    elif email_sent:
        logger.info("EmailProducer: sent heartbeat (no new articles)")
    else:
        logger.error("EmailProducer: send failed")

    return {"email_sent": email_sent}
