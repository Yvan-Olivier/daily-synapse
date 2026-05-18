"""EmailProducer node — sends daily digest from curated articles in State.

Filters state["articles"] to those that are approved and not yet emailed,
so previously-emailed Articles aren't re-sent if they happen to be in
state (e.g. carried over because the Podcast stage hadn't completed).
On Resend failure, `emailed_at` stays NULL so the Resumer retries
next run.
"""
import logging

from app.database.repository import Repository
from app.email.sender import send_digest
from app.graph.state import PipelineState

logger = logging.getLogger(__name__)


def email_producer_node(state: PipelineState, repo: Repository) -> dict:
    to_email = [
        a for a in state["articles"]
        if a.critic_approved and a.emailed_at is None
    ]
    email_sent = send_digest(to_email)

    if email_sent and to_email:
        repo.mark_articles_emailed([a.guid for a in to_email])
        logger.info("EmailProducer: sent digest with %d article(s)", len(to_email))
    elif email_sent:
        logger.info("EmailProducer: sent heartbeat (no new articles)")
    else:
        logger.error("EmailProducer: send failed — articles remain pending for next run")

    return {"email_sent": email_sent}
