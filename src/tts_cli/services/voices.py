from typing import Optional
import edge_tts


async def list_voices(language: Optional[str] = None, gender: Optional[str] = None, search: Optional[str] = None) -> None:
    voices = await edge_tts.list_voices()
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
