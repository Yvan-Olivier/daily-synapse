"""PodcastProducer node — generates script + MP3 from curated articles in State.

Filters state["articles"] to those that are approved and not yet
podcasted. On TTS failure the script is persisted but `podcasted_at`
stays NULL — the Resumer brings the Article back for retry next run.
"""
import logging
from datetime import date
from pathlib import Path

from app.database.repository import Repository
from app.graph.state import PipelineState
from app.llm.script_writer import ScriptWriter
from app.podcast.tts_client import OpenAITTSClient

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("output/podcasts")


def podcast_producer_node(state: PipelineState, repo: Repository) -> dict:
    to_podcast = [
        a for a in state["articles"]
        if a.critic_approved and a.podcasted_at is None
    ]
    today = date.today()
    mp3_path = OUTPUT_DIR / f"daily-synapse-{today}.mp3"

    if mp3_path.exists():
        logger.info("PodcastProducer: episode already exists — skipping")
        return {"podcast_mp3": str(mp3_path)}

    if not to_podcast:
        logger.info("PodcastProducer: no articles to podcast — skipping episode")
        return {"podcast_mp3": None}

    # TTS retry: script already in DB but MP3 missing
    pending = repo.get_pending_tts_episode(today)
    if pending:
        logger.info("PodcastProducer: retrying TTS (script already in DB)")
        script = pending.script
        article_guids = pending.article_guids
    else:
        writer = ScriptWriter()
        script = writer.write_script(articles=to_podcast, episode_date=today)
        if not script:
            logger.error("PodcastProducer: script generation failed")
            return {"podcast_mp3": None}

        article_guids = [a.guid for a in to_podcast]
        repo.save_podcast_episode(
            episode_date=today, script=script, article_guids=article_guids
        )
        logger.info("PodcastProducer: script saved (%d words)", len(script.split()))

    tts = OpenAITTSClient()
    ok = tts.synthesize(script=script, output_path=mp3_path)

    if ok:
        repo.update_podcast_mp3(episode_date=today, mp3_path=str(mp3_path))
        repo.mark_articles_podcasted(article_guids)
        logger.info("PodcastProducer: MP3 ready at %s", mp3_path)
        return {"podcast_mp3": str(mp3_path)}

    logger.error("PodcastProducer: TTS failed — script saved, retry next run")
    return {"podcast_mp3": None}
