from tts_cli.services.voices import list_voices


class VoiceListingUseCase:
    async def execute(self, *args, **kwargs) -> None:
        await list_voices(*args, **kwargs)
