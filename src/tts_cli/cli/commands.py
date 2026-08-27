from pathlib import Path
from uuid import uuid4

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
from tts_cli.adapters.subtitle.srt import cues_to_srt
from tts_cli.application.composition import create_batch_dependencies, create_synthesis, create_transcription, create_voice_catalog
from tts_cli.application.bus import CommandBus, ExecuteOperation
from tts_cli.application.bus import EventBus
from tts_cli.core.events import OperationCompleted, OperationFailed, ProgressUpdated
from tts_cli.core.events import ApplicationNotice
from tts_cli.adapters.console.progress import ProgressBar
from tts_cli.adapters.console.events import ConsoleNoticeRenderer
from tts_cli.adapters.input.resolver import InputResolver


async def async_main(args) -> int:
    command_bus = CommandBus()
    if args.command == "voices":
        result = await VoiceListingUseCase(create_voice_catalog(args.engine)).execute(
            args.language, args.gender, args.search,
        )
        if not result:
            print("Không tìm thấy voice.")
            return 0
        print(f"{'VOICE':<40}{'LOCALE':<12}{'GENDER':<10}")
        print("-" * 62)
        for voice in result:
            print(f"{voice.get('ShortName', ''):<40}{voice.get('Locale', ''):<12}{voice.get('Gender', ''):<10}")
        print(f"\nTổng: {len(result)} voice")
        return 0
    if args.command == "generate":
        validate_args(args)
        if args.text is not None and args.file:
            raise ValueError("Không thể dùng --text và --file cùng lúc.")
        config = TTSConfig(args.voice, args.rate, args.pitch, args.volume, args.retries, args.timeout, args.proxy)
        event_bus = EventBus()
        operation_id = str(uuid4())
        renderer: ProgressBar | None = None
        notice_renderer = ConsoleNoticeRenderer()

        def render(event: ProgressUpdated | OperationCompleted | OperationFailed) -> None:
            nonlocal renderer
            if isinstance(event, ProgressUpdated):
                if renderer is None:
                    renderer = ProgressBar(event.total, "Generate")
                renderer.update(event.current, event.stage)
            elif renderer is not None:
                renderer.finish()

        event_bus.subscribe(ProgressUpdated, render)
        event_bus.subscribe(OperationCompleted, render)
        event_bus.subscribe(OperationFailed, render)
        event_bus.subscribe(ApplicationNotice, notice_renderer)
        command_bus = CommandBus(event_bus)
        synthesis = create_synthesis(config, args.engine, event_bus=event_bus, operation_id=operation_id)
        await command_bus.dispatch(ExecuteOperation(lambda: synthesis.execute(
            InputResolver().resolve(args).text, Path(args.output), args.subtitle_mode,
            args.max_words, args.start, args.overwrite, args.dry_run, formats=args.formats,
        ), operation_id))
        return 0
    if args.command == "batch":
        validate_args(args)
        config = TTSConfig(args.voice, args.rate, args.pitch, args.volume, args.retries, args.timeout, args.proxy)
        synthesis = create_synthesis(config, args.engine)
        batch_files, input_resolver, output_resolver, progress = create_batch_dependencies()
        await command_bus.dispatch(ExecuteOperation(lambda: BatchProcessUseCase(synthesis, batch_files, input_resolver, output_resolver, progress).execute(
            Path(args.directory), Path(args.output), args.recursive,
            args.subtitle_mode, args.max_words, args.start, args.skip_existing,
            args.continue_on_error, args.dry_run, args.formats,
        )))
        return 0
    if args.command == "transcribe":
        source = Path(args.source)
        if not source.is_file():
            raise FileNotFoundError(f"Không tìm thấy file media: {source}")
        if not is_audio_file(source) and not is_video_file(source):
            raise ValueError(f"Định dạng media không được hỗ trợ: {source.suffix}")
        transcribe_config = TranscribeConfig(args.model_size, args.language, args.device)
        transcription = await create_transcription(transcribe_config)
        await command_bus.dispatch(ExecuteOperation(lambda: TranscribeUseCase(transcription, cues_to_srt).execute(source, Path(args.output))))
        print(f"✅ TRANSCRIBE: {args.output}")
        return 0
    return 2


def normalize_argv(argv: list[str]) -> list[str]:
    commands = {"generate", "batch", "voices", "transcribe", "-h", "--help", "--version"}
    if argv and argv[0] not in commands and any(option in argv for option in ("-t", "--text", "-f", "--file")):
        return ["generate", *argv]
    return argv
