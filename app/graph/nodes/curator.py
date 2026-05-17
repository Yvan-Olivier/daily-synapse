"""Curator node — ranks approved articles by relevance to user profile."""
import logging
from typing import List

from pydantic import BaseModel

from app.graph.state import PipelineState
from app.llm.base import OllamaBase

logger = logging.getLogger(__name__)

USER_PROFILE = (
    "Senior AI engineer interested in AI safety, LLM research, and applied AI systems."
)

CURATOR_SYSTEM_PROMPT = f"""You are a content curator for an AI news platform.

Target reader: {USER_PROFILE}

For each article provided, assign a relevance score from 1 (not relevant) to 10 (highly relevant).
Return scores for ALL articles. Higher score = more valuable to the reader."""


class ArticleScore(BaseModel):
    guid: str
    score: int


class CuratorOutput(BaseModel):
    scores: List[ArticleScore]


class CuratorAgent(OllamaBase):
    def rank(self, articles: list) -> list:
        if not articles:
            return articles

        articles_block = "\n\n".join(
            f"guid: {a.guid}\ntitle: {a.summary_title or a.title}\nsummary: {a.summary}"
            for a in articles
        )
        user_prompt = f"Rate these articles:\n\n{articles_block}"

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": CURATOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                format=CuratorOutput.model_json_schema(),
                options={"temperature": 0.2},
                think=False,
            )
            output = CuratorOutput.model_validate_json(response.message.content)
            score_map = {s.guid: s.score for s in output.scores}
            ranked = sorted(articles, key=lambda a: score_map.get(a.guid, 0), reverse=True)
            logger.info(
                "Curator: ranked %d articles (top: '%s')",
                len(ranked),
                ranked[0].summary_title or ranked[0].title if ranked else "—",
            )
            return ranked
        except Exception as exc:
            logger.error("Curator failed: %s — returning unsorted", exc)
            return articles


def curator_node(state: PipelineState) -> dict:
    agent = CuratorAgent()
    ranked = agent.rank(state["articles"])
    return {"articles": ranked}
