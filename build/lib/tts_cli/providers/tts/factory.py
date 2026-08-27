from collections.abc import Callable
from typing import Any

from tts_cli.core.interfaces import TTSEngine
from tts_cli.providers.tts.google import GoogleTTSEngine
from tts_cli.providers.tts.edge import EdgeTTSEngine
from tts_cli.providers.tts.edge import EdgeTTSEngine


class TTSProviderFactory:
    _providers: dict[str, Callable[[Any], TTSEngine]] = {
        "edge": EdgeTTSEngine,
        "google": GoogleTTSEngine,
    }

    @classmethod
    def register(cls, name: str, provider: Callable[[Any], TTSEngine]) -> None:
        normalized_name = name.strip().lower()
        if not normalized_name:
            raise ValueError("Tên TTS engine không được rỗng.")
        cls._providers[normalized_name] = provider

    @classmethod
    def create(cls, name: str, config: Any) -> TTSEngine:
        normalized_name = name.strip().lower()
        try:
            provider = cls._providers[normalized_name]
        except KeyError as exc:
            available = ", ".join(sorted(cls._providers))
            raise ValueError(f"TTS engine không hỗ trợ: {name}. Có sẵn: {available}") from exc
        return provider(config)