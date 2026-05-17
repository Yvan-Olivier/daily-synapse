"""Unit tests for the Critic agent."""
from unittest.mock import MagicMock, patch

from app.graph.nodes.critic import CriticAgent, CriticVerdict


def test_critic_approves_faithful_summary():
    agent = CriticAgent()
    mock_response = MagicMock()
    mock_response.message.content = (
        '{"approved": true, "reason": "Summary accurately reflects the article."}'
    )

    with patch.object(agent.client, "chat", return_value=mock_response):
        verdict = agent.verify(
            title="Claude 3.5 Sonnet Released",
            content="Anthropic released Claude 3.5 Sonnet with improved reasoning.",
            summary="Anthropic releases Claude 3.5 Sonnet with enhanced reasoning.",
        )

    assert verdict is not None
    assert verdict.approved is True


def test_critic_rejects_hallucinated_summary():
    agent = CriticAgent()
    mock_response = MagicMock()
    mock_response.message.content = (
        '{"approved": false, "reason": "Summary claims 1T parameters not in article."}'
    )

    with patch.object(agent.client, "chat", return_value=mock_response):
        verdict = agent.verify(
            title="Claude 3.5 Sonnet Released",
            content="Anthropic released Claude 3.5 Sonnet, a new model.",
            summary="Anthropic releases Claude 3.5 Sonnet with 1 trillion parameters.",
        )

    assert verdict is not None
    assert verdict.approved is False
    assert "1T" in verdict.reason


def test_critic_returns_none_on_failure():
    agent = CriticAgent()

    with patch.object(agent.client, "chat", side_effect=Exception("Connection refused")):
        verdict = agent.verify(
            title="Test article",
            content="Some content",
            summary="Some summary",
        )

    assert verdict is None
