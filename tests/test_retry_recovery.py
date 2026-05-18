"""Retry / recovery tests.

Pin the M3 contract that no Article is silently lost when something
fails downstream of the Summarizer. Two failure modes are covered:

1. Critic API failure must NOT mark the Article as rejected; it must
   leave `criticized_at` NULL so the Resumer picks it up next run.
2. EmailProducer / Resend failure must NOT stamp `emailed_at`; the
   Resumer picks the Article up next run.

Also covers the related skip-when-already-processed paths.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.graph.nodes.critic import CriticVerdict, critic_node
from app.graph.nodes.email_producer import email_producer_node


class FakeArticle:
    """Minimal stand-in for AnthropicArticle ORM object."""

    def __init__(
        self,
        guid,
        title="t",
        description="c",
        summary="s",
        summary_title="st",
        criticized_at=None,
        critic_approved=None,
        emailed_at=None,
        podcasted_at=None,
    ):
        self.guid = guid
        self.title = title
        self.description = description
        self.summary = summary
        self.summary_title = summary_title
        self.criticized_at = criticized_at
        self.critic_approved = critic_approved
        self.emailed_at = emailed_at
        self.podcasted_at = podcasted_at


def _state(articles):
    return {
        "hours": 48,
        "articles": articles,
        "rejected_count_this_run": 0,
        "email_sent": False,
        "podcast_mp3": None,
        "errors": [],
    }


# --- Critic --------------------------------------------------------------

def test_critic_api_failure_leaves_article_retryable():
    """API failure -> no DB write, no rejection counted, article excluded
    from this run but criticized_at stays NULL so the Resumer retries."""
    article = FakeArticle(guid="g1")
    repo = MagicMock()

    with patch("app.graph.nodes.critic.CriticAgent.__init__", return_value=None), \
         patch("app.graph.nodes.critic.CriticAgent.verify", return_value=None):
        result = critic_node(_state([article]), repo)

    assert article not in result["articles"]
    assert result["rejected_count_this_run"] == 0
    repo.set_critic_verdict.assert_not_called()


def test_critic_legitimate_rejection_is_persisted():
    """Verdict=False -> persisted in DB so the Article is never retried."""
    article = FakeArticle(guid="g1")
    repo = MagicMock()
    rejection = CriticVerdict(approved=False, reason="hallucination")

    with patch("app.graph.nodes.critic.CriticAgent.__init__", return_value=None), \
         patch("app.graph.nodes.critic.CriticAgent.verify", return_value=rejection):
        result = critic_node(_state([article]), repo)

    assert article not in result["articles"]
    assert result["rejected_count_this_run"] == 1
    repo.set_critic_verdict.assert_called_once_with("g1", False)


def test_critic_approval_is_persisted_and_keeps_article():
    """Verdict=True -> persisted; article continues downstream."""
    article = FakeArticle(guid="g1")
    repo = MagicMock()
    approval = CriticVerdict(approved=True, reason="faithful")

    with patch("app.graph.nodes.critic.CriticAgent.__init__", return_value=None), \
         patch("app.graph.nodes.critic.CriticAgent.verify", return_value=approval):
        result = critic_node(_state([article]), repo)

    assert article in result["articles"]
    assert result["rejected_count_this_run"] == 0
    repo.set_critic_verdict.assert_called_once_with("g1", True)


def test_critic_skips_already_evaluated_approved_article():
    """Resurrected approved article -> no API call, no DB write,
    article passes through to downstream nodes."""
    article = FakeArticle(
        guid="g1",
        criticized_at=datetime.now(timezone.utc),
        critic_approved=True,
    )
    repo = MagicMock()

    with patch("app.graph.nodes.critic.CriticAgent.__init__", return_value=None), \
         patch("app.graph.nodes.critic.CriticAgent.verify") as verify_mock:
        result = critic_node(_state([article]), repo)

    verify_mock.assert_not_called()
    repo.set_critic_verdict.assert_not_called()
    assert article in result["articles"]


# --- EmailProducer -------------------------------------------------------

def test_email_send_failure_does_not_mark_articles_emailed():
    """Resend returns False -> emailed_at stays NULL, Resumer retries."""
    article = FakeArticle(guid="g1", critic_approved=True, emailed_at=None)
    repo = MagicMock()

    with patch("app.graph.nodes.email_producer.send_digest", return_value=False):
        result = email_producer_node(_state([article]), repo)

    assert result["email_sent"] is False
    repo.mark_articles_emailed.assert_not_called()


def test_email_producer_filters_out_already_emailed_articles():
    """An already-emailed article in state must not be re-sent."""
    fresh = FakeArticle(guid="fresh", critic_approved=True, emailed_at=None)
    done = FakeArticle(
        guid="done",
        critic_approved=True,
        emailed_at=datetime.now(timezone.utc),
    )
    repo = MagicMock()
    captured = []

    def capture(arts):
        captured.extend(arts)
        return True

    with patch("app.graph.nodes.email_producer.send_digest", side_effect=capture):
        result = email_producer_node(_state([fresh, done]), repo)

    assert result["email_sent"] is True
    assert [a.guid for a in captured] == ["fresh"]
    repo.mark_articles_emailed.assert_called_once_with(["fresh"])
