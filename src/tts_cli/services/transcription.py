import tempfile
from pathlib import Path

from tts_cli.adapters.input.media import is_video_file
from tts_cli.core.interfaces import MediaProcessor, SpeechTranscriber
from tts_cli.core.models import TranscriptResult


class TranscriptionService:
    def __init__(self, transcriber: SpeechTranscriber, media: MediaProcessor):
        self.transcriber = transcriber
        self.media = media

    async def execute(self, source: Path) -> TranscriptResult:
        temporary_audio: Path | None = None
        audio_path = Path(source)
        if is_video_file(audio_path):
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temporary_file:
                temporary_audio = Path(temporary_file.name)
            await self.media.extract_audio(audio_path, temporary_audio)
            audio_path = temporary_audio
        try:
            return await self.transcriber.transcribe(audio_path)
        finally:
            if temporary_audio is not None:
                temporary_audio.unlink(missing_ok=True)
