
__all__ = ["VoiceCatalogService"]
from collections.abc import Awaitable, Callable
from typing import Any


class VoiceCatalogService:
    def __init__(self, loader: Callable[[], Awaitable[list[dict[str, Any]]]]):
        self.loader = loader

    async def find(
        self,
        language: str | None = None,
        gender: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        voices = await self.loader()
        result = []
        for voice in voices:
            short_name = str(voice.get("ShortName", ""))
            locale = str(voice.get("Locale", ""))
            voice_gender = str(voice.get("Gender", ""))
            friendly_name = str(voice.get("FriendlyName", ""))
            if language and not (locale.lower().startswith(language.lower()) or language.lower() in short_name.lower()):
                continue
            if gender and voice_gender.lower() != gender.lower():
                continue
            if search and search.lower() not in f"{short_name} {locale} {friendly_name}".lower():
                continue
            result.append(voice)
        return sorted(result, key=lambda item: (item.get("Locale", ""), item.get("ShortName", "")))
