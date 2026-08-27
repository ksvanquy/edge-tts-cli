import asyncio
from pathlib import Path

from tts_cli.application.transcribe import TranscribeUseCase
from tts_cli.adapters.subtitle.srt import cues_to_srt
from tts_cli.core.models import SubtitleCue, TranscriptResult
from tts_cli.services.transcription import TranscriptionService


class FakeTranscriber:
    name = "fake"

    async def transcribe(self, audio_path: Path) -> TranscriptResult:
        assert audio_path.suffix == ".wav"
        return TranscriptResult([SubtitleCue(0, 1_000, "Hello")], "en-US")


class FakeMedia:
    async def extract_audio(self, source: Path, destination: Path) -> None:
        destination.write_bytes(b"wav")

    async def probe(self, source: Path) -> dict[str, object]:
        return {}


def test_transcribe_extracts_video_audio_and_writes_srt(tmp_path: Path):
    source = tmp_path / "input.mp4"
    source.write_bytes(b"video")
    output = tmp_path / "subtitle.srt"

    transcription = TranscriptionService(FakeTranscriber(), FakeMedia())
    result = asyncio.run(TranscribeUseCase(transcription, cues_to_srt).execute(source, output))

    assert result.language == "en-US"
    assert output.read_text(encoding="utf-8") == "1\n00:00:00,000 --> 00:00:00,001\nHello\n"