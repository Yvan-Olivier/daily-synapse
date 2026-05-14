"""Daily Synapse — M0 entry point.

Run the daily pipeline: scrape Anthropic RSS feeds, store in Postgres,
summarize each article via Ollama.

Usage:
    python main.py            # Use default lookback (48h)
    python main.py 24         # Custom lookback in hours
"""
import sys

from dotenv import load_dotenv

load_dotenv()

from app.services.process_summaries import run_pipeline


def main(hours: int = 48) -> dict:
    return run_pipeline(hours=hours)


if __name__ == "__main__":
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 48
    result = main(hours=hours)
    sys.exit(0 if result["success"] else 1)
