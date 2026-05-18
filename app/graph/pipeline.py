"""LangGraph pipeline — wires all nodes into the daily processing graph.

Graph:
    Scraper → Summarizer → Critic → Curator → EmailProducer → PodcastProducer
"""
import logging
from datetime import datetime

from langgraph.graph import END, StateGraph

from app.config import DEFAULT_LOOKBACK_HOURS
from app.database.repository import Repository
from app.graph.nodes.critic import critic_node
from app.graph.nodes.curator import curator_node
from app.graph.nodes.email_producer import email_producer_node
from app.graph.nodes.podcast_producer import podcast_producer_node
from app.graph.nodes.scraper import scraper_node
from app.graph.nodes.summarizer import summarizer_node
from app.graph.state import PipelineState

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_graph(repo: Repository):
    """Compile the StateGraph with repo injected via closure."""
    graph = StateGraph(PipelineState)

    graph.add_node("scraper", lambda s: scraper_node(s, repo))
    graph.add_node("summarizer", lambda s: summarizer_node(s, repo))
    graph.add_node("critic", lambda s: critic_node(s, repo))
    graph.add_node("curator", curator_node)
    graph.add_node("email_producer", lambda s: email_producer_node(s, repo))
    graph.add_node("podcast_producer", lambda s: podcast_producer_node(s, repo))

    graph.set_entry_point("scraper")
    graph.add_edge("scraper", "summarizer")
    graph.add_edge("summarizer", "critic")
    graph.add_edge("critic", "curator")
    graph.add_edge("curator", "email_producer")
    graph.add_edge("email_producer", "podcast_producer")
    graph.add_edge("podcast_producer", END)

    return graph.compile()


def run_graph(hours: int = DEFAULT_LOOKBACK_HOURS) -> dict:
    """Run the full pipeline. Returns final PipelineState + success flag."""
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("Daily Synapse — pipeline starting")
    logger.info("=" * 60)

    repo = Repository()
    try:
        graph = build_graph(repo)
        initial_state: PipelineState = {
            "hours": hours,
            "articles": [],
            "rejected": [],
            "email_sent": False,
            "podcast_mp3": None,
            "errors": [],
        }
        final_state = graph.invoke(initial_state)
        duration = (datetime.now() - start).total_seconds()

        logger.info("=" * 60)
        logger.info("Pipeline finished in %.1fs", duration)
        logger.info("  Articles:  %d approved, %d rejected", len(final_state["articles"]), len(final_state["rejected"]))
        logger.info("  Email:     %s", "sent" if final_state["email_sent"] else "failed")
        logger.info("  Podcast:   %s", final_state["podcast_mp3"] or "skipped/failed")
        if final_state["errors"]:
            logger.warning("  Errors:    %s", final_state["errors"])
        logger.info("=" * 60)

        return {"success": True, **final_state}
    except Exception as exc:
        logger.error("Pipeline crashed: %s", exc, exc_info=True)
        return {"success": False, "error": str(exc)}
    finally:
        repo.close()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    repo = Repository()
    print(build_graph(repo).get_graph().draw_mermaid())
    repo.close()
