"""Resend email sender for the Daily Synapse digest."""
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import resend
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR), autoescape=True)

SENDER = "Daily Synapse <onboarding@resend.dev>"


def send_digest(articles: List) -> bool:
    """Render and send the daily digest email.

    Returns True if the email was accepted by Resend, False otherwise.
    """
    api_key = os.getenv("RESEND_API_KEY", "")
    recipient = os.getenv("DIGEST_EMAIL", "")

    if not api_key or not recipient:
        logger.error("RESEND_API_KEY or DIGEST_EMAIL is not set — skipping email")
        return False

    resend.api_key = api_key

    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    n = len(articles)
    subject = (
        f"Daily Synapse · {date_str} · {n} new article{'s' if n != 1 else ''}"
        if articles
        else f"Daily Synapse · {date_str} · No new articles"
    )

    template = _jinja_env.get_template("digest.html")
    html = template.render(articles=articles, date=date_str)

    try:
        resend.Emails.send({
            "from": SENDER,
            "to": [recipient],
            "subject": subject,
            "html": html,
        })
        logger.info("Digest sent to %s (%d articles)", recipient, n)
        return True
    except Exception as exc:
        logger.error("Failed to send digest: %s", exc)
        return False
