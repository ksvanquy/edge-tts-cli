from pathlib import Path

from tts_cli.core.config import validate_args
from tts_cli.core.models import TTSConfig
from tts_cli.services.batch import BatchService
from tts_cli.services.tts import TTSService
from tts_cli.services.voices import list_voices
from tts_cli.text.resolver import InputResolver


async def async_main(args) -> int:
    if args.command == "voices":
        await list_voices(args.language, args.gender, args.search)
        return 0
    if args.command == "generate":
        validate_args(args)
        if args.text is not None and args.file:
            raise ValueError("Không thể dùng --text và --file cùng lúc.")
        config = TTSConfig(args.voice, args.rate, args.pitch, args.volume, args.retries, args.timeout, args.proxy)
        service = TTSService(config)
        await service.generate(
            InputResolver().resolve(args).text, Path(args.output), args.subtitle_mode,
            args.max_words, args.start, args.overwrite, args.dry_run, formats=args.formats,
        )
        return 0
    if args.command == "batch":
        validate_args(args)
        config = TTSConfig(args.voice, args.rate, args.pitch, args.volume, args.retries, args.timeout, args.proxy)
        await BatchService(TTSService(config)).process(
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
