import asyncio
from collections.abc import Callable
from pathlib import Path

from tts_cli.core.interfaces import OutputPort, ProgressPort, ProjectPort, RetryPort, TTSEngine
from tts_cli.core.models import OutputContext, SubtitleCue, SynthesisResult, TTSConfig


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

    async def synthesize_with_retry(self, text: str, audio_path: Path) -> SynthesisResult:
        async def operation() -> SynthesisResult:
            result = await self.engine.synthesize(text, audio_path)
            if not isinstance(result, SynthesisResult):
                raise TypeError("TTS provider phải trả về SynthesisResult.")
            return result

        return await self.retry.execute(operation, self.config.retries, self.config.timeout, audio_path)

    @staticmethod
    async def _animate_tts_progress(progress: ProgressPort) -> None:
        current = 1
        while current <= 70:
            progress.update(current, "TTS")
            current += 1
            await asyncio.sleep(0.08)

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
            print(f"  → {folder}/")
            for index, handler in enumerate(handlers):
                branch = "└──" if index == len(handlers) - 1 else "├──"
                print(f"     {branch} {self.output.filename(handler)}")
            return number
        if folder.exists() and not overwrite:
            raise FileExistsError(f"Folder output đã tồn tại: {folder}")
        folder_created = not folder.exists()
        folder.mkdir(parents=True, exist_ok=True)
        progress = self.progress_factory(100, "Generate")
        progress.update(0, "TTS")
        try:
            progress_task = asyncio.create_task(self._animate_tts_progress(progress)) if progress.enabled else None
            try:
                synthesis_result = await self.synthesize_with_retry(text, audio_path)
            finally:
                if progress_task is not None:
                    progress_task.cancel()
                    try:
                        await progress_task
                    except asyncio.CancelledError:
                        pass
            word_cues = synthesis_result.word_cues
            progress.update(75, "subtitle")
            subtitle_cues = self.subtitle_builder(word_cues, subtitle_mode, max_words)
            progress.update(90, "output")
            self.output.write(OutputContext(folder, word_cues, subtitle_cues, audio_path), formats)
            progress.update(100, "hoàn tất")
        except Exception:
            self.output.cleanup(folder, formats, remove_folder=folder_created)
            raise
        finally:
            progress.finish()
        duration = self.format_duration(word_cues[-1].end) if word_cues else "0.00s"
        print(f"✅ PROJECT {number:03d}: {len(word_cues)} từ, {len(subtitle_cues)} cues, {duration}")
        return number


__all__ = ["SynthesizeUseCase"]
