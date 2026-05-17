"""Daily Synapse — M3 entry point.

Run the daily pipeline: scrape → summarize → critic → curate → email + podcast.

Usage:
    python main.py            # default lookback (48h)
    python main.py 168        # custom lookback in hours
"""
import sys

from dotenv import load_dotenv

load_dotenv()

from app.graph.pipeline import run_graph


def main(hours: int = 48) -> dict:
    return run_graph(hours=hours)


if __name__ == "__main__":
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 48
    result = main(hours=hours)
    sys.exit(0 if result["success"] else 1)
