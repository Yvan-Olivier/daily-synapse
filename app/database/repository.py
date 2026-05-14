"""Repository pattern for DB access.

All DB reads/writes go through this module — no SQLAlchemy queries
anywhere else in the codebase.
"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from .connection import get_session
from .models import AnthropicArticle


class Repository:
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()

    # --- Anthropic articles --------------------------------------------------

    def bulk_insert_anthropic_articles(self, articles: List[dict]) -> int:
        """Insert articles, skipping any whose guid already exists.

        Returns the count of newly inserted rows.
        """
        new_count = 0
        for a in articles:
            existing = (
                self.session.query(AnthropicArticle)
                .filter_by(guid=a["guid"])
                .first()
            )
            if existing:
                continue

            article = AnthropicArticle(
                guid=a["guid"],
                title=a["title"],
                url=a["url"],
                description=a.get("description"),
                published_at=a["published_at"],
                category=a.get("category"),
            )
            self.session.add(article)
            new_count += 1

        if new_count:
            self.session.commit()
        return new_count

    def get_articles_without_summary(
        self, limit: Optional[int] = None
    ) -> List[AnthropicArticle]:
        """Return all articles whose summary is still NULL (idempotency-friendly)."""
        query = self.session.query(AnthropicArticle).filter(
            AnthropicArticle.summary.is_(None)
        )
        if limit:
            query = query.limit(limit)
        return query.all()

    def update_summary(
        self, guid: str, summary_title: str, summary: str
    ) -> bool:
        article = (
            self.session.query(AnthropicArticle).filter_by(guid=guid).first()
        )
        if not article:
            return False

        article.summary_title = summary_title
        article.summary = summary
        article.summarized_at = datetime.now(timezone.utc)
        self.session.commit()
        return True

    def get_articles_for_digest(self) -> List[AnthropicArticle]:
        """Return summarized articles not yet included in a digest."""
        return (
            self.session.query(AnthropicArticle)
            .filter(
                AnthropicArticle.summary.isnot(None),
                AnthropicArticle.emailed_at.is_(None),
            )
            .order_by(AnthropicArticle.published_at.desc())
            .all()
        )

    def mark_articles_emailed(self, guids: List[str]) -> None:
        """Stamp emailed_at on all articles included in the sent digest."""
        now = datetime.now(timezone.utc)
        for guid in guids:
            article = self.session.query(AnthropicArticle).filter_by(guid=guid).first()
            if article:
                article.emailed_at = now
        self.session.commit()

    # --- Lifecycle -----------------------------------------------------------

    def close(self):
        self.session.close()
