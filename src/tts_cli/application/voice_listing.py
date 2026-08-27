from tts_cli.core.interfaces import VoiceCatalogPort


class VoiceListingUseCase:
    def __init__(self, catalog: VoiceCatalogPort):
        self.catalog = catalog

    async def execute(
        self,
        language: str | None = None,
        gender: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, str]]:
        return await self.catalog.find(language, gender, search)
