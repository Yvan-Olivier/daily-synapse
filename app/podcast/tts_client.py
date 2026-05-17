"""TTS client abstraction — swappable between providers.

M2: OpenAITTSClient (Azure for Students blocks Speech Services regions)
M8: AzureTTSClient to be added here when deploying to Azure
"""
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path

from openai import OpenAI

logger = logging.getLogger(__name__)


class TTSClient(ABC):
    @abstractmethod
    def synthesize(self, script: str, output_path: Path) -> bool:
        """Convert script to MP3 at output_path. Returns True on success."""


class OpenAITTSClient(TTSClient):
    def __init__(self, voice: str | None = None, model: str = "tts-1"):
        self.voice = voice or os.getenv("PODCAST_VOICE", "nova")
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def synthesize(self, script: str, output_path: Path) -> bool:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=self.voice,
                input=script,
            ) as response:
                response.stream_to_file(output_path)
            logger.info("MP3 saved to %s", output_path)
            return True
        except Exception as exc:
            logger.error("TTS synthesis failed: %s", exc)
            return False
