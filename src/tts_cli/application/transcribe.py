import tempfile
from pathlib import Path

from tts_cli.core.models import TranscriptResult
from tts_cli.core.interfaces import MediaProcessor, SpeechTranscriber
from tts_cli.subtitle.srt import cues_to_srt


class TranscribeUseCase:
    """Convert an audio or video source into an SRT transcript."""

    def __init__(self, transcriber: SpeechTranscriber, media: MediaProcessor):
        self.transcriber = transcriber
        self.media = media

    async def execute(self, source: Path, output_path: Path) -> TranscriptResult:
        source = Path(source)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_audio: Path | None = None
        audio_path = source
        if source.suffix.lower() in {".mp4", ".mkv", ".mov", ".webm", ".avi"}:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temporary_file:
                temporary_audio = Path(temporary_file.name)
            audio_path = temporary_audio
            await self.media.extract_audio(source, audio_path)
        try:
            result = await self.transcriber.transcribe(audio_path)
            output_path.write_text(cues_to_srt(result.cues), encoding="utf-8", newline="\n")
            return result
        finally:
            if temporary_audio is not None:
                temporary_audio.unlink(missing_ok=True)
