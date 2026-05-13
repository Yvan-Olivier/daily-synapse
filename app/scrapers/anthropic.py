"""Anthropic RSS scraper.

Anthropic does not publish an official RSS feed, so we use the three
community-maintained feeds (news, research, engineering) from the
Olshansk/rss-feeds repository.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import feedparser
from pydantic import BaseModel

from app.config import ANTHROPIC_RSS_FEEDS


class AnthropicArticle(BaseModel):
    """Scraper-side article model (Pydantic).

    Decoupled from the SQLAlchemy ORM model so scrapers can run
    independently and be tested in isolation.
    """
    title: str
    description: str
    url: str
    guid: str
    published_at: datetime
    category: Optional[str] = None


class AnthropicScraper:
    def __init__(self):
        self.rss_urls = ANTHROPIC_RSS_FEEDS

    def get_articles(self, hours: int = 48) -> List[AnthropicArticle]:
        """Fetch and deduplicate articles from all Anthropic RSS feeds.

        Args:
            hours: Lookback window in hours. Articles older than this
                are skipped.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        seen: set[str] = set()
        articles: List[AnthropicArticle] = []

        for rss_url in self.rss_urls:
            feed = feedparser.parse(rss_url)
            if not feed.entries:
                continue

            for entry in feed.entries:
                published_parsed = getattr(entry, "published_parsed", None)
                if not published_parsed:
                    continue

                published_time = datetime(
                    *published_parsed[:6], tzinfo=timezone.utc
                )
                if published_time < cutoff:
                    continue

                guid = entry.get("id") or entry.get("link", "")
                if not guid or guid in seen:
                    continue
                seen.add(guid)

                category = None
                tags = entry.get("tags", [])
                if tags and isinstance(tags, list):
                    category = tags[0].get("term") if tags[0] else None

                articles.append(
                    AnthropicArticle(
                        title=entry.get("title", ""),
                        description=entry.get("description", ""),
                        url=entry.get("link", ""),
                        guid=guid,
                        published_at=published_time,
                        category=category,
                    )
                )

        return articles


if __name__ == "__main__":
    scraper = AnthropicScraper()
    articles = scraper.get_articles(hours=72)
    print(f"Found {len(articles)} articles in the last 72h\n")
    for a in articles[:5]:
        print(f"  [{a.published_at.date()}] {a.title}")
        print(f"    {a.url}\n")
