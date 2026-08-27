"""Application composition helpers shared by CLI and desktop clients."""

from tts_cli.adapters.console.progress import ProgressBar
from tts_cli.adapters.input.processor import normalize_text
from tts_cli.adapters.input.resolver import InputResolver
from tts_cli.adapters.output.resolver import OutputResolver
from tts_cli.adapters.subtitle.cues import build_subtitle_cues
from tts_cli.adapters.subtitle.srt import format_duration
from tts_cli.application.synthesize import SynthesizeUseCase
from tts_cli.core.models import TTSConfig, TranscribeConfig
from tts_cli.providers.media import get_media_processor
from tts_cli.providers.stt.factory import STTProviderFactory
from tts_cli.providers.tts.factory import TTSProviderFactory
from tts_cli.providers.tts.voice_catalog import voice_loader
from tts_cli.services.batch_files import BatchFileService
from tts_cli.services.project import ProjectService
from tts_cli.services.retry import RetryExecutor
from tts_cli.services.transcription import TranscriptionService
from tts_cli.services.voice_catalog import VoiceCatalogService
from collections.abc import Callable
from tts_cli.core.interfaces import ProgressPort
from tts_cli.application.bus import EventBus, EventProgress


def create_synthesis(
    config: TTSConfig,
    engine: str,
    progress_factory: Callable[[int, str], ProgressPort] = ProgressBar,
    event_bus: EventBus | None = None,
    operation_id: str | None = None,
) -> SynthesizeUseCase:
    if event_bus is not None and operation_id is not None:
        progress_factory = lambda total, label: EventProgress(total, label, event_bus, operation_id)
    return SynthesizeUseCase(
        TTSProviderFactory.create(engine, config), config, RetryExecutor(), ProjectService(),
        OutputResolver(), normalize_text, build_subtitle_cues, format_duration, progress_factory,
        event_bus, operation_id,
    )


def create_batch_dependencies(
    progress_factory: Callable[[int, str], ProgressPort] = ProgressBar,
) -> tuple[BatchFileService, InputResolver, OutputResolver, Callable[[int, str], ProgressPort]]:
    return BatchFileService(), InputResolver(), OutputResolver(), progress_factory


async def create_transcription(config: TranscribeConfig) -> TranscriptionService:
    transcriber = STTProviderFactory.create("whisper", config)
    return TranscriptionService(transcriber, await get_media_processor())


def create_voice_catalog(engine: str) -> VoiceCatalogService:
    return VoiceCatalogService(voice_loader(engine))
