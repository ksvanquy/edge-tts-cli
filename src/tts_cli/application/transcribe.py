from pathlib import Path
from collections.abc import Callable

from tts_cli.core.interfaces import TranscriptionPort
from tts_cli.core.models import TranscriptResult


class TranscribeUseCase:
    """Convert an audio or video source into an SRT transcript."""

    def __init__(self, transcription: TranscriptionPort, subtitle_writer: Callable[[list], str]):
        self.transcription = transcription
        self.subtitle_writer = subtitle_writer

    async def execute(self, source: Path, output_path: Path) -> TranscriptResult:
        source = Path(source)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result = await self.transcription.execute(source)
        output_path.write_text(self.subtitle_writer(result.cues), encoding="utf-8", newline="\n")
        return result
