"""PipelineState — the single object that flows through the LangGraph pipeline."""
import operator
from typing import Annotated

from typing_extensions import TypedDict


class PipelineState(TypedDict):
    hours: int                              # lookback window for the scraper
    articles: list                          # AnthropicArticle ORM objects — evolves through nodes
    rejected_count_this_run: int            # tally of new rejections produced by the Critic this run
    email_sent: bool
    podcast_mp3: str | None
    errors: Annotated[list, operator.add]   # accumulates across nodes
