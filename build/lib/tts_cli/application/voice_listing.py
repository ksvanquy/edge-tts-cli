from tts_cli.core.interfaces import VoiceCatalogPort


class VoiceListingUseCase:
    def __init__(self, catalog: VoiceCatalogPort):
        self.catalog = catalog

    async def execute(
        self,
        language: str | None = None,
        gender: str | None = None,
        search: str | None = None,
    ) -> None:
        result = await self.catalog.find(language, gender, search)
        if not result:
            print("Không tìm thấy voice.")
            return
        print(f"{'VOICE':<40}{'LOCALE':<12}{'GENDER':<10}")
        print("-" * 62)
        for voice in result:
            print(f"{voice.get('ShortName', ''):<40}{voice.get('Locale', ''):<12}{voice.get('Gender', ''):<10}")
        print(f"\nTổng: {len(result)} voice")
