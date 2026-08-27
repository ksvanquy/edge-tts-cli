import asyncio
from typing import Optional
import edge_tts


async def list_voices(
    language: Optional[str] = None,
    gender: Optional[str] = None,
    search: Optional[str] = None,
    engine: str = "edge",
) -> None:
    if engine == "edge":
        voices = await edge_tts.list_voices()
    elif engine == "google":
        voices = await _list_google_voices()
    else:
        raise ValueError(f"TTS engine không hỗ trợ: {engine}")
    result = []
    for voice in voices:
        short_name = voice.get("ShortName", "")
        locale = voice.get("Locale", "")
        voice_gender = voice.get("Gender", "")
        friendly_name = voice.get("FriendlyName", "")
        if language and not (locale.lower().startswith(language.lower()) or language.lower() in short_name.lower()):
            continue
        if gender and voice_gender.lower() != gender.lower():
            continue
        if search and search.lower() not in f"{short_name} {locale} {friendly_name}".lower():
            continue
        result.append(voice)
    result.sort(key=lambda item: (item.get("Locale", ""), item.get("ShortName", "")))
    if not result:
        print("Không tìm thấy voice.")
        return
    print(f"{'VOICE':<40}{'LOCALE':<12}{'GENDER':<10}")
    print("-" * 62)
    for voice in result:
        print(f"{voice.get('ShortName', ''):<40}{voice.get('Locale', ''):<12}{voice.get('Gender', ''):<10}")
    print(f"\nTổng: {len(result)} voice")


async def _list_google_voices() -> list[dict[str, str]]:
    try:
        from google.cloud import texttospeech
    except ImportError as exc:
        raise RuntimeError(
            "Google TTS chưa được cài. Dùng `pip install .[google]`."
        ) from exc

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
