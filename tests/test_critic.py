"""Unit tests for the Critic agent."""
from unittest.mock import MagicMock

from app.graph.nodes.critic import CriticAgent, CriticVerdict


def _make_agent_with_mock(parsed_output):
    agent = CriticAgent.__new__(CriticAgent)
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.parsed = parsed_output
    mock_client.beta.chat.completions.parse.return_value = mock_response
    agent.client = mock_client
    return agent


def test_critic_approves_faithful_summary():
    verdict_obj = CriticVerdict(approved=True, reason="Summary accurately reflects the article.")
    agent = _make_agent_with_mock(verdict_obj)

    verdict = agent.verify(
        title="Claude 3.5 Sonnet Released",
        content="Anthropic released Claude 3.5 Sonnet with improved reasoning.",
        summary="Anthropic releases Claude 3.5 Sonnet with enhanced reasoning.",
    )

    assert verdict is not None
    assert verdict.approved is True


def test_critic_rejects_hallucinated_summary():
    verdict_obj = CriticVerdict(approved=False, reason="Summary claims 1T parameters not in article.")
    agent = _make_agent_with_mock(verdict_obj)

    verdict = agent.verify(
        title="Claude 3.5 Sonnet Released",
        content="Anthropic released Claude 3.5 Sonnet, a new model.",
        summary="Anthropic releases Claude 3.5 Sonnet with 1 trillion parameters.",
    )

    assert verdict is not None
    assert verdict.approved is False
    assert "1T" in verdict.reason


def test_critic_returns_none_on_failure():
    agent = CriticAgent.__new__(CriticAgent)
    mock_client = MagicMock()
    mock_client.beta.chat.completions.parse.side_effect = Exception("Connection refused")
    agent.client = mock_client

    verdict = agent.verify(
        title="Test article",
        content="Some content",
        summary="Some summary",
    )

    assert verdict is None
