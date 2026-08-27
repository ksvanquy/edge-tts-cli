import asyncio
from collections.abc import Callable
from pathlib import Path

from tts_cli.core.interfaces import OutputPort, ProgressPort, ProjectPort, RetryPort, TTSEngine
from tts_cli.core.models import OutputContext, SubtitleCue, SynthesisResult, TTSConfig
from tts_cli.application.bus import EventBus
from tts_cli.core.events import ApplicationNotice


class SynthesizeUseCase:
    """Orchestrate text normalization, synthesis, subtitles, and output."""

    def __init__(
        self,
        engine: TTSEngine,
        config: TTSConfig,
        retry: RetryPort,
        projects: ProjectPort,
        output: OutputPort,
        normalize: Callable[[str], str],
        subtitle_builder: Callable[[list[SubtitleCue], str, int], list[SubtitleCue]],
        format_duration: Callable[[int], str],
        progress_factory: Callable[[int, str], ProgressPort],
        event_bus: EventBus | None = None,
        operation_id: str | None = None,
    ):
        self.engine = engine
        self.config = config
        self.retry = retry
        self.projects = projects
        self.output = output
        self.normalize = normalize
        self.subtitle_builder = subtitle_builder
        self.format_duration = format_duration
        self.progress_factory = progress_factory
        self.event_bus = event_bus
        self.operation_id = operation_id

    def _notify(self, level: str, message: str) -> None:
        if self.event_bus is not None:
            self.event_bus.publish(ApplicationNotice(self.operation_id, level, message))
        else:
            print(message)

    async def synthesize_with_retry(self, text: str, audio_path: Path) -> SynthesisResult:
        async def operation() -> SynthesisResult:
            result = await self.engine.synthesize(text, audio_path)
            if not isinstance(result, SynthesisResult):
                raise TypeError("TTS provider phải trả về SynthesisResult.")
            return result

        return await self.retry.execute(operation, self.config.retries, self.config.timeout, audio_path)

    async def execute(
        self, text: str, output_root: Path, subtitle_mode: str, max_words: int,
        start: int = 1, overwrite: bool = False, dry_run: bool = False,
        project_number: int | None = None, formats: str | list[str] | None = None,
    ) -> int:
        text = self.normalize(text)
        if not text:
            raise ValueError("Text rỗng.")
        handlers = self.output.resolve(formats)
        output_root.mkdir(parents=True, exist_ok=True)
        project = self.projects.paths(output_root, start, project_number)
        number, folder, audio_path = project.number, project.folder, project.audio
        if dry_run:
            self._notify("info", f"  → {folder}/")
            for index, handler in enumerate(handlers):
                branch = "└──" if index == len(handlers) - 1 else "├──"
                self._notify("info", f"     {branch} {self.output.filename(handler)}")
            return number
        if folder.exists() and not overwrite:
            raise FileExistsError(f"Folder output đã tồn tại: {folder}")
        folder_created = not folder.exists()
        folder.mkdir(parents=True, exist_ok=True)
        progress = self.progress_factory(100, "Generate")
        self._notify("debug", f"Bắt đầu project {number:03d}: {len(text)} ký tự")
        progress.update(0, "TTS")
        try:
            synthesis_result = await self.synthesize_with_retry(text, audio_path)
            self._notify("debug", f"TTS trả về {len(synthesis_result.word_cues)} word cues")
            progress.update(70, "TTS hoàn tất")
            word_cues = synthesis_result.word_cues
            progress.update(80, "subtitle")
            subtitle_cues = self.subtitle_builder(word_cues, subtitle_mode, max_words)
            self._notify("debug", f"Đã dựng {len(subtitle_cues)} subtitle cues")
            progress.update(95, "output")
            self.output.write(OutputContext(folder, word_cues, subtitle_cues, audio_path), formats)
            self._notify("debug", f"Đã ghi output: {folder}")
            progress.update(100, "hoàn tất")
        except Exception as error:
            if self.event_bus is not None and self.operation_id is not None:
                self._notify("error", f"Project {number:03d} thất bại: {error}")
            self.output.cleanup(folder, formats, remove_folder=folder_created)
            raise
        finally:
            progress.finish()
        duration = self.format_duration(word_cues[-1].end) if word_cues else "0.00s"
        self._notify("info", f"✅ PROJECT {number:03d}: {len(word_cues)} từ, {len(subtitle_cues)} cues, {duration}")
        return number


__all__ = ["SynthesizeUseCase"]
