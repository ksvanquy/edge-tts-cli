from pathlib import Path
from typing import Protocol

from tts_cli.core.models import ProviderCapabilities, SynthesisResult, TranscriptResult


class TTSEngine(Protocol):
    capabilities: ProviderCapabilities

    async def synthesize(self, text: str, audio_path: Path) -> SynthesisResult:
        ...


class SpeechTranscriber(Protocol):
    name: str

    async def transcribe(self, audio_path: Path) -> TranscriptResult:
        ...


class MediaProcessor(Protocol):
    async def extract_audio(self, source: Path, destination: Path) -> None:
        ...

    async def probe(self, source: Path) -> dict[str, object]:
        ...


__all__ = ["MediaProcessor", "SpeechTranscriber", "TTSEngine"]
