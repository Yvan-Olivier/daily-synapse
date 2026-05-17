"""PipelineState — the single object that flows through the LangGraph pipeline."""
import operator
from typing import Annotated

from typing_extensions import TypedDict


class PipelineState(TypedDict):
    hours: int                              # lookback window for the scraper
    articles: list                          # AnthropicArticle ORM objects — evolves through nodes
    rejected: list                          # guids rejected by the Critic
    email_sent: bool
    podcast_mp3: str | None
    errors: Annotated[list, operator.add]   # accumulates across nodes
