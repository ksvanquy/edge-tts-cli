from pathlib import Path

from tts_cli.core.config import validate_args
from tts_cli.core.models import TTSConfig
from tts_cli.application.batch_process import BatchProcessUseCase
from tts_cli.application.synthesize import SynthesizeUseCase
from tts_cli.application.voice_listing import VoiceListingUseCase
from tts_cli.application.transcribe import TranscribeUseCase
from tts_cli.core.models import TranscribeConfig
from tts_cli.adapters.input.media import is_audio_file, is_video_file
from tts_cli.adapters.input.processor import normalize_text
from tts_cli.adapters.output.resolver import OutputResolver
from tts_cli.adapters.subtitle.cues import build_subtitle_cues
from tts_cli.adapters.subtitle.srt import cues_to_srt, format_duration
from tts_cli.adapters.console.progress import ProgressBar
from tts_cli.providers.stt.factory import STTProviderFactory
from tts_cli.providers.tts.factory import TTSProviderFactory
from tts_cli.providers.tts.voice_catalog import voice_loader
from tts_cli.adapters.input.resolver import InputResolver
from tts_cli.providers.media import get_media_processor
from tts_cli.services.voice_catalog import VoiceCatalogService
from tts_cli.services.batch_files import BatchFileService
from tts_cli.services.project import ProjectService
from tts_cli.services.retry import RetryExecutor
from tts_cli.services.transcription import TranscriptionService


def create_synthesis(config: TTSConfig, engine: str) -> SynthesizeUseCase:
    return SynthesizeUseCase(
        TTSProviderFactory.create(engine, config), config, RetryExecutor(), ProjectService(),
        OutputResolver(), normalize_text, build_subtitle_cues, format_duration, ProgressBar,
    )


async def async_main(args) -> int:
    if args.command == "voices":
        catalog = VoiceCatalogService(voice_loader(args.engine))
        await VoiceListingUseCase(catalog).execute(args.language, args.gender, args.search)
        return 0
    if args.command == "generate":
        validate_args(args)
        if args.text is not None and args.file:
            raise ValueError("Không thể dùng --text và --file cùng lúc.")
        config = TTSConfig(args.voice, args.rate, args.pitch, args.volume, args.retries, args.timeout, args.proxy)
        synthesis = create_synthesis(config, args.engine)
        await synthesis.execute(
            InputResolver().resolve(args).text, Path(args.output), args.subtitle_mode,
            args.max_words, args.start, args.overwrite, args.dry_run, formats=args.formats,
        )
        return 0
    if args.command == "batch":
        validate_args(args)
        config = TTSConfig(args.voice, args.rate, args.pitch, args.volume, args.retries, args.timeout, args.proxy)
        synthesis = create_synthesis(config, args.engine)
        await BatchProcessUseCase(
            synthesis, BatchFileService(), InputResolver(), OutputResolver(), ProgressBar,
        ).execute(
            Path(args.directory), Path(args.output), args.recursive,
            args.subtitle_mode, args.max_words, args.start, args.skip_existing,
            args.continue_on_error, args.dry_run, args.formats,
        )
        return 0
    if args.command == "transcribe":
        source = Path(args.source)
        if not source.is_file():
            raise FileNotFoundError(f"Không tìm thấy file media: {source}")
        if not is_audio_file(source) and not is_video_file(source):
            raise ValueError(f"Định dạng media không được hỗ trợ: {source.suffix}")
        config = TranscribeConfig(args.model_size, args.language, args.device)
        transcriber = STTProviderFactory.create(args.engine, config)
        media = await get_media_processor()
        await TranscribeUseCase(TranscriptionService(transcriber, media), cues_to_srt).execute(source, Path(args.output))
        print(f"✅ TRANSCRIBE: {args.output}")
        return 0
    return 2


def normalize_argv(argv: list[str]) -> list[str]:
    commands = {"generate", "batch", "voices", "transcribe", "-h", "--help", "--version"}
    if argv and argv[0] not in commands and any(option in argv for option in ("-t", "--text", "-f", "--file")):
        return ["generate", *argv]
    return argv
