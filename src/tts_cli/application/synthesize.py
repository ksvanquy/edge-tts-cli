import asyncio
from pathlib import Path

from tts_cli.console.printer import print_warning
from tts_cli.console.progress import ProgressBar
from tts_cli.core.interfaces import TTSEngine
from tts_cli.core.models import SubtitleCue, SynthesisResult, TTSConfig
from tts_cli.input.processor import normalize_text
from tts_cli.output.formats import OutputContext
from tts_cli.output.project import get_next_number
from tts_cli.output.resolver import OutputResolver
from tts_cli.subtitle.cues import build_subtitle_cues
from tts_cli.subtitle.srt import format_duration


class SynthesizeUseCase:
    """Orchestrate text normalization, synthesis, subtitles, and output."""

    def __init__(self, engine: TTSEngine, config: TTSConfig):
        self.engine = engine
        self.config = config

    async def synthesize_with_retry(self, text: str, audio_path: Path) -> SynthesisResult:
        total_attempts = self.config.retries + 1
        last_error = None
        for attempt in range(1, total_attempts + 1):
            print(f"  🎙️ TTS {attempt}/{total_attempts}")
            try:
                result = await asyncio.wait_for(self.engine.synthesize(text, audio_path), timeout=self.config.timeout)
                if not isinstance(result, SynthesisResult):
                    raise TypeError("TTS provider phải trả về SynthesisResult.")
                return result
            except Exception as exc:
                last_error = exc
                if audio_path.exists():
                    try:
                        audio_path.unlink()
                    except OSError as unlink_error:
                        print_warning(f"Không thể xóa audio lỗi: {unlink_error}")
                if attempt < total_attempts:
                    wait_seconds = min(2 ** (attempt - 1), 10)
                    print_warning(f"TTS lỗi: {exc}")
                    print(f"  🔄 Retry sau {wait_seconds}s...")
                    await asyncio.sleep(wait_seconds)
        raise RuntimeError(f"Không thể tạo audio sau {total_attempts} lần thử: {last_error}")

    @staticmethod
    async def _animate_tts_progress(progress: ProgressBar) -> None:
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
        text = normalize_text(text)
        if not text:
            raise ValueError("Text rỗng.")
        output_resolver = OutputResolver()
        handlers = output_resolver.resolve(formats)
        output_root.mkdir(parents=True, exist_ok=True)
        number = project_number if project_number is not None else get_next_number(output_root, start)
        folder = output_root / f"{number:03d}"
        audio_path = folder / "audio.mp3"
        if dry_run:
            print(f"  → {folder}/")
            for index, handler in enumerate(handlers):
                branch = "└──" if index == len(handlers) - 1 else "├──"
                print(f"     {branch} {output_resolver.filename(handler)}")
            return number
        if folder.exists() and not overwrite:
            raise FileExistsError(f"Folder output đã tồn tại: {folder}")
        folder_created = not folder.exists()
        folder.mkdir(parents=True, exist_ok=True)
        progress = ProgressBar(100, "Generate")
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
            subtitle_cues = build_subtitle_cues(word_cues, subtitle_mode, max_words)
            progress.update(90, "output")
            output_resolver.write(OutputContext(folder, word_cues, subtitle_cues, audio_path), formats)
            progress.update(100, "hoàn tất")
        except Exception:
            output_resolver.cleanup(folder, formats, remove_folder=folder_created)
            raise
        finally:
            progress.finish()
        duration = format_duration(word_cues[-1].end) if word_cues else "0.00s"
        print(f"✅ PROJECT {number:03d}: {len(word_cues)} từ, {len(subtitle_cues)} cues, {duration}")
        return number


__all__ = ["SynthesizeUseCase"]
