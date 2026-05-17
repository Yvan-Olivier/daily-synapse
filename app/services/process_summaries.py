"""End-to-end pipeline orchestrator (M0 → M2).

Pipeline:
    1. Scrape Anthropic RSS feeds
    2. Insert new articles into Postgres (skip duplicates)
    3. Summarize every article that doesn't yet have a summary via Ollama
    4. Send the daily digest email via Resend, mark articles as emailed
    5. Produce the daily podcast episode (script via Ollama + MP3 via TTS)

The pipeline is idempotent: running it twice in a row produces
0 inserts, 0 summaries, 0 emails, and 0 new episodes on the second run.
"""
import logging
from datetime import datetime

from app.config import DEFAULT_LOOKBACK_HOURS
from app.database.repository import Repository
from app.email.sender import send_digest
from app.llm.ollama_client import OllamaClient
from app.podcast.producer import produce_episode
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
    logger.info("Daily Synapse — pipeline starting")
    logger.info("=" * 60)

    result = {
        "start_time": start.isoformat(),
        "scraped": 0,
        "inserted": 0,
        "existing": 0,
        "summarized": 0,
        "failed": 0,
        "emailed": 0,
        "email_success": False,
        "podcast_skipped": False,
        "podcast_mp3": None,
        "success": False,
    }

    repo: Repository | None = None

    try:
        scraper = AnthropicScraper()
        repo = Repository()
        llm = OllamaClient()

        # 1. Scrape ----------------------------------------------------------
        logger.info("[1/4] Scraping Anthropic RSS (last %sh)...", hours)
        articles = scraper.get_articles(hours=hours)
        result["scraped"] = len(articles)
        logger.info("      Found %d articles in feeds", len(articles))

        # 2. Persist new articles -------------------------------------------
        logger.info("[2/4] Storing new articles in Postgres...")
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
        logger.info("[3/4] Summarizing pending articles via Ollama...")
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

        # 4. Send digest email -------------------------------------------------
        logger.info("[4/4] Sending digest email...")
        digest_articles = repo.get_articles_for_digest()
        result["emailed"] = len(digest_articles)
        email_sent = send_digest(digest_articles)
        result["email_success"] = email_sent
        if email_sent and digest_articles:
            repo.mark_articles_emailed([a.guid for a in digest_articles])

        # 5. Produce podcast episode -------------------------------------------
        logger.info("[5/5] Producing podcast episode...")
        pod = produce_episode(repo=repo)
        result["podcast_skipped"] = pod["skipped"]
        result["podcast_mp3"] = pod.get("mp3_path")
        if pod["skipped"]:
            logger.info("      Skipped (no new articles or already done)")
        elif pod["tts_ok"]:
            logger.info("      MP3 ready: %s", pod["mp3_path"])
        else:
            logger.warning("      TTS failed — script saved, will retry next run")

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
    logger.info(
        "  Emailed:    %d (sent: %s)",
        result["emailed"],
        result["email_success"],
    )
    logger.info(
        "  Podcast:    %s",
        result["podcast_mp3"] or ("skipped" if result["podcast_skipped"] else "TTS failed — retry next run"),
    )
    logger.info("=" * 60)

    return result


if __name__ == "__main__":
    run_pipeline()
