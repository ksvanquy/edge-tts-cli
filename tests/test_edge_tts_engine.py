import asyncio
from pathlib import Path

from tts_cli.core.models import SubtitleCue, TTSConfig
from tts_cli.providers.tts.edge import EdgeTTSEngine


def test_edge_tts_engine_writes_audio_and_collects_word_boundaries(tmp_path: Path, monkeypatch):
    class FakeCommunicate:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def stream(self):
            async def chunks():
                yield {"type": "audio", "data": b"audio"}
                yield {"type": "WordBoundary", "offset": "10000000", "duration": "5000000", "text": "Xin"}
                yield {"type": "WordBoundary", "offset": "bad", "duration": 1, "text": "loi"}
                yield {"type": "WordBoundary", "offset": 0, "duration": 1, "text": "  "}
                yield {"type": "metadata", "data": "ignored"}

            return chunks()

    monkeypatch.setattr("tts_cli.providers.tts.edge.edge_tts.Communicate", FakeCommunicate)
    audio_path = tmp_path / "audio.mp3"
    config = TTSConfig("vi-VN-NamMinhNeural", "+0%", "+0Hz", "+0%", 0, 1.0, None)

    result = asyncio.run(EdgeTTSEngine(config).synthesize("Xin", audio_path))

    assert audio_path.read_bytes() == b"audio"
    assert result.word_cues == [SubtitleCue(1_000_000, 1_500_000, "Xin")]
    assert result.metadata == {"provider": "edge"}