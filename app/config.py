"""Central configuration for Daily Synapse."""

# Anthropic — 3 community-maintained RSS feeds
ANTHROPIC_RSS_FEEDS = [
    "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
    "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
    "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
]

# Default lookback window for each pipeline run
DEFAULT_LOOKBACK_HOURS = 48
