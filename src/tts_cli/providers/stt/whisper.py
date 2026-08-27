"""Local speech-to-text provider backed by faster-whisper."""

import asyncio
from pathlib import Path

from tts_cli.core.models import ProviderCapabilities, TranscriptResult, TranscribeConfig, SubtitleCue


class WhisperTranscriber:
    name = "whisper"
    capabilities = ProviderCapabilities(sentence_timing=True)

    def __init__(self, config: TranscribeConfig | None = None):
        self.config = config or TranscribeConfig()

    async def transcribe(self, audio_path: Path) -> TranscriptResult:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "Whisper STT chưa được cài. Dùng `pip install .[whisper]`."
            ) from exc

        config = self.config
        model = await asyncio.to_thread(
            WhisperModel,
            config.model_size,
            device=self._device(config.device),
            compute_type=self._compute_type(config.compute_type, config.device),
        )
        cues, language = await asyncio.to_thread(self._transcribe, model, audio_path, config.language)
        return TranscriptResult(cues, language, {"provider": self.name, "model_size": config.model_size})

    @staticmethod
    def _transcribe(model, audio_path: Path, language: str | None):
        segments, info = model.transcribe(str(audio_path), language=language)
        cues = [
            SubtitleCue(int(segment.start * 1000), int(segment.end * 1000), segment.text.strip())
            for segment in segments
            if segment.text.strip()
        ]
        return cues, info.language

    @staticmethod
    def _device(device: str) -> str:
        if device == "auto":
            return "cpu"
        if device not in {"cpu", "cuda"}:
            raise ValueError(f"Thiết bị Whisper không hợp lệ: {device}")
        return device

    @staticmethod
    def _compute_type(compute_type: str, device: str) -> str:
        if compute_type != "auto":
            return compute_type
        return "float16" if device == "cuda" else "int8"


__all__ = ["WhisperTranscriber"]
