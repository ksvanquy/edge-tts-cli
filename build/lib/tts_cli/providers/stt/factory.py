from collections.abc import Callable
from typing import Any

from tts_cli.core.interfaces import SpeechTranscriber
from tts_cli.providers.stt.whisper import WhisperTranscriber


class STTProviderFactory:
    _providers: dict[str, Callable[[Any], SpeechTranscriber]] = {
        "whisper": WhisperTranscriber,
    }

    @classmethod
    def register(cls, name: str, provider: Callable[[Any], SpeechTranscriber]) -> None:
        normalized_name = name.strip().lower()
        if not normalized_name:
            raise ValueError("Tên STT engine không được rỗng.")
        cls._providers[normalized_name] = provider

    @classmethod
    def create(cls, name: str, config: Any = None) -> SpeechTranscriber:
        normalized_name = name.strip().lower()
        try:
            provider = cls._providers[normalized_name]
        except KeyError as exc:
            available = ", ".join(sorted(cls._providers)) or "chưa có"
            raise ValueError(f"STT engine không hỗ trợ: {name}. Có sẵn: {available}") from exc
        return provider(config)
