from pathlib import Path

from tts_cli.core.config import validate_args
from tts_cli.core.models import TTSConfig
from tts_cli.application.batch_process import BatchProcessUseCase
from tts_cli.application.synthesize import SynthesizeUseCase
from tts_cli.application.voice_listing import VoiceListingUseCase
from tts_cli.providers.tts.factory import TTSProviderFactory
from tts_cli.input.resolver import InputResolver


async def async_main(args) -> int:
    if args.command == "voices":
        await VoiceListingUseCase().execute(args.language, args.gender, args.search, args.engine)
        return 0
    if args.command == "generate":
        validate_args(args)
        if args.text is not None and args.file:
            raise ValueError("Không thể dùng --text và --file cùng lúc.")
        config = TTSConfig(args.voice, args.rate, args.pitch, args.volume, args.retries, args.timeout, args.proxy)
        synthesis = SynthesizeUseCase(TTSProviderFactory.create(args.engine, config), config)
        await synthesis.execute(
            InputResolver().resolve(args).text, Path(args.output), args.subtitle_mode,
            args.max_words, args.start, args.overwrite, args.dry_run, formats=args.formats,
        )
        return 0
    if args.command == "batch":
        validate_args(args)
        config = TTSConfig(args.voice, args.rate, args.pitch, args.volume, args.retries, args.timeout, args.proxy)
        synthesis = SynthesizeUseCase(TTSProviderFactory.create(args.engine, config), config)
        await BatchProcessUseCase(synthesis).execute(
            Path(args.directory), Path(args.output), args.recursive,
            args.subtitle_mode, args.max_words, args.start, args.skip_existing,
            args.continue_on_error, args.dry_run, args.formats,
        )
        return 0
    return 2


def normalize_argv(argv: list[str]) -> list[str]:
    commands = {"generate", "batch", "voices", "-h", "--help", "--version"}
    if argv and argv[0] not in commands and any(option in argv for option in ("-t", "--text", "-f", "--file")):
        return ["generate", *argv]
    return argv
