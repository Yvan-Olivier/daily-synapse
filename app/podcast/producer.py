"""Podcast episode producer — orchestrates script generation and TTS.

Pipeline for one episode:
    1. Check if today's episode already exists (idempotency)
    2. If script missing: generate via Ollama ScriptWriter
    3. Persist episode (script + NULL mp3_path) in DB
    4. Convert script to MP3 via TTS client
    5. Update episode with mp3_path, stamp podcasted_at on articles
"""
import logging
from datetime import date, datetime, timezone
from pathlib import Path

from app.database.models import AnthropicArticle
from app.database.repository import Repository
from app.llm.script_writer import ScriptWriter
from app.podcast.tts_client import OpenAITTSClient, TTSClient

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("output/podcasts")


def produce_episode(
    repo: Repository,
    tts_client: TTSClient | None = None,
) -> dict:
    """Produce the daily podcast episode.

    Returns a dict with keys: skipped, script_ok, tts_ok, mp3_path.
    """
    result = {"skipped": False, "script_ok": False, "tts_ok": False, "mp3_path": None}
    today = date.today()
    mp3_path = OUTPUT_DIR / f"daily-synapse-{today}.mp3"

    # --- Idempotency: episode fully done already ----------------------------
    if mp3_path.exists():
        logger.info("Episode for %s already exists — skipping", today)
        result["skipped"] = True
        result["tts_ok"] = True
        result["mp3_path"] = str(mp3_path)
        return result

    # --- Check for TTS retry (script in DB but no MP3) ---------------------
    pending = repo.get_pending_tts_episode(today)
    if pending:
        logger.info("Retrying TTS for %s (script already in DB)", today)
        script = pending.script
        article_guids = pending.article_guids
    else:
        # --- Fetch articles pending podcast --------------------------------
        articles = repo.get_articles_for_podcast()
        if not articles:
            logger.info("No articles pending podcast — skipping episode")
            result["skipped"] = True
            return result

        # --- Generate script -----------------------------------------------
        logger.info("Generating podcast script for %d article(s)...", len(articles))
        writer = ScriptWriter()
        script = writer.write_script(articles=articles, episode_date=today)
        if not script:
            logger.error("Script generation failed — aborting episode")
            return result
        result["script_ok"] = True

        # --- Persist episode (script only, mp3_path NULL) ------------------
        article_guids = [a.guid for a in articles]
        repo.save_podcast_episode(
            episode_date=today,
            script=script,
            article_guids=article_guids,
        )
        logger.info("Episode persisted (script saved, awaiting TTS)")

    result["script_ok"] = True

    # --- TTS ---------------------------------------------------------------
    client = tts_client or OpenAITTSClient()
    logger.info("Synthesizing audio via TTS...")
    tts_ok = client.synthesize(script=script, output_path=mp3_path)

    if tts_ok:
        repo.update_podcast_mp3(episode_date=today, mp3_path=str(mp3_path))
        repo.mark_articles_podcasted(article_guids)
        result["tts_ok"] = True
        result["mp3_path"] = str(mp3_path)
        logger.info("Episode complete: %s", mp3_path)
    else:
        logger.error("TTS failed — script saved, will retry on next run")

    return result
