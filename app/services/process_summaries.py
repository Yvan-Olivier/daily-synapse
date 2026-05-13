"""End-to-end M0 pipeline orchestrator.

Pipeline:
    1. Scrape Anthropic RSS feeds
    2. Insert new articles into Postgres (skip duplicates)
    3. Summarize every article that doesn't yet have a summary via Ollama
    4. Store the generated summary back into Postgres

The pipeline is idempotent: running it twice in a row produces
0 inserts and 0 summaries on the second run.
"""
import logging
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from app.config import DEFAULT_LOOKBACK_HOURS
from app.database.repository import Repository
from app.llm.ollama_client import OllamaClient
from app.scrapers.anthropic import AnthropicScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline(hours: int = DEFAULT_LOOKBACK_HOURS) -> dict:
    """Run the full M0 pipeline.

    Returns a dict with execution metrics; exit code in main.py is based
    on the boolean `success` key.
    """
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("Daily Synapse — M0 pipeline starting")
    logger.info("=" * 60)

    result = {
        "start_time": start.isoformat(),
        "scraped": 0,
        "inserted": 0,
        "existing": 0,
        "summarized": 0,
        "failed": 0,
        "success": False,
    }

    repo: Repository | None = None

    try:
        scraper = AnthropicScraper()
        repo = Repository()
        llm = OllamaClient()

        # 1. Scrape ----------------------------------------------------------
        logger.info("[1/3] Scraping Anthropic RSS (last %sh)...", hours)
        articles = scraper.get_articles(hours=hours)
        result["scraped"] = len(articles)
        logger.info("      Found %d articles in feeds", len(articles))

        # 2. Persist new articles -------------------------------------------
        logger.info("[2/3] Storing new articles in Postgres...")
        article_dicts = [a.model_dump() for a in articles]
        inserted = repo.bulk_insert_anthropic_articles(article_dicts)
        result["inserted"] = inserted
        result["existing"] = len(articles) - inserted
        logger.info(
            "      Inserted %d new article(s) (%d already existed)",
            inserted,
            result["existing"],
        )

        # 3. Summarize pending articles -------------------------------------
        logger.info("[3/3] Summarizing pending articles via Ollama...")
        pending = repo.get_articles_without_summary()
        logger.info("      %d article(s) pending summarization", len(pending))

        for idx, article in enumerate(pending, 1):
            short = (
                article.title[:60] + "..."
                if len(article.title) > 60
                else article.title
            )
            logger.info("      [%d/%d] %s", idx, len(pending), short)

            content = article.description or article.title
            summary_output = llm.summarize(title=article.title, content=content)

            if summary_output is None:
                result["failed"] += 1
                logger.warning("            -> FAILED")
                continue

            repo.update_summary(
                guid=article.guid,
                summary_title=summary_output.title,
                summary=summary_output.summary,
            )
            result["summarized"] += 1
            logger.info("            -> %s", summary_output.title)

        result["success"] = True

    except Exception as exc:
        logger.error("Pipeline crashed: %s", exc, exc_info=True)
        result["error"] = str(exc)

    finally:
        if repo is not None:
            repo.close()

    duration = (datetime.now() - start).total_seconds()
    result["duration_seconds"] = duration

    logger.info("=" * 60)
    logger.info("Pipeline finished in %.1fs", duration)
    logger.info(
        "  Scraped:    %d  |  Inserted: %d (existing: %d)",
        result["scraped"],
        result["inserted"],
        result["existing"],
    )
    logger.info(
        "  Summarized: %d (failed: %d)",
        result["summarized"],
        result["failed"],
    )
    logger.info("=" * 60)

    return result


if __name__ == "__main__":
    run_pipeline()
