"""Critic node — validates each summary against its source article."""
import logging
from typing import Optional

from pydantic import BaseModel

from app.database.repository import Repository
from app.graph.state import PipelineState
from app.llm.base import OllamaBase

logger = logging.getLogger(__name__)


class CriticVerdict(BaseModel):
    approved: bool
    reason: str


CRITIC_SYSTEM_PROMPT = """You are a fact-checking agent for an AI news platform.

Given an article and its generated summary, determine if the summary is accurate and faithful.

Rules:
- APPROVED: the summary accurately reflects the article content with no hallucinations
- REJECTED: the summary contains claims absent from the article, or misrepresents it

Minor paraphrasing is fine. Fabricated details are not. Be strict but fair."""


class CriticAgent(OllamaBase):
    def verify(
        self, title: str, content: str, summary: str
    ) -> Optional[CriticVerdict]:
        user_prompt = (
            f"Article title: {title}\n\n"
            f"Article content:\n{content[:3000]}\n\n"
            f"Generated summary: {summary}"
        )
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                format=CriticVerdict.model_json_schema(),
                options={"temperature": 0.1},
                think=False,
            )
            return CriticVerdict.model_validate_json(response.message.content)
        except Exception as exc:
            logger.error("Critic failed for '%s': %s", title[:60], exc)
            return None


def critic_node(state: PipelineState, repo: Repository) -> dict:
    agent = CriticAgent()
    articles = state["articles"]
    approved = []
    rejected = list(state["rejected"])
    errors = []

    for article in articles:
        content = article.description or article.title
        verdict = agent.verify(
            title=article.title,
            content=content,
            summary=article.summary or "",
        )

        if verdict is None:
            errors.append(f"Critic call failed for {article.guid}")
            logger.warning("Critic: call FAILED for '%s' — discarding", article.title[:60])
            rejected.append(article.guid)
            continue

        if verdict.approved:
            approved.append(article)
            logger.info("Critic: APPROVED '%s'", article.title[:60])
        else:
            rejected.append(article.guid)
            logger.warning(
                "Critic: REJECTED '%s' — %s", article.title[:60], verdict.reason
            )

    logger.info("Critic: %d approved, %d rejected", len(approved), len(rejected))
    return {"articles": approved, "rejected": rejected, "errors": errors}
