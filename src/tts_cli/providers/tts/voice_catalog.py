"""Voice catalog adapters for supported TTS providers."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


async def list_edge_voices() -> list[dict[str, Any]]:
    import edge_tts

    return await edge_tts.list_voices()


async def list_google_voices() -> list[dict[str, str]]:
    try:
        from google.cloud import texttospeech
    except ImportError as exc:
        raise RuntimeError("Google TTS chưa được cài. Dùng `pip install .[google]`.") from exc

    client = texttospeech.TextToSpeechClient()
    response = await asyncio.to_thread(client.list_voices)
    return [
        {
            "ShortName": voice.name,
            "Locale": voice.language_codes[0] if voice.language_codes else "",
            "Gender": texttospeech.SsmlVoiceGender(voice.ssml_gender).name.title(),
            "FriendlyName": voice.name,
        }
        for voice in response.voices
    ]


def voice_loader(engine: str) -> Callable[[], Awaitable[list[dict[str, Any]]]]:
    loaders = {"edge": list_edge_voices, "google": list_google_voices}
    try:
        return loaders[engine]
    except KeyError as exc:
        raise ValueError(f"TTS engine không hỗ trợ: {engine}") from exc


__all__ = ["list_edge_voices", "list_google_voices", "voice_loader"]
