from pathlib import Path
from collections.abc import Callable

from tts_cli.application.synthesize import SynthesizeUseCase
from tts_cli.core.interfaces import BatchFilesPort, InputPort, OutputPort, ProgressPort


class BatchProcessUseCase:
    """Discover input files and orchestrate batch synthesis."""

    def __init__(
        self,
        synthesis: SynthesizeUseCase,
        files: BatchFilesPort,
        inputs: InputPort,
        output: OutputPort,
        progress_factory: Callable[[int, str], ProgressPort],
    ):
        self.synthesis = synthesis
        self.files = files
        self.inputs = inputs
        self.output = output
        self.progress_factory = progress_factory

    async def execute(
        self, source: Path, output_root: Path, recursive: bool, subtitle_mode: str,
        max_words: int, start: int, skip_existing: bool, continue_on_error: bool,
        dry_run: bool, formats: str | list[str] | None = None,
    ) -> None:
        if not source.exists():
            raise FileNotFoundError(f"Không tìm thấy thư mục: {source}")
        if not source.is_dir():
            raise ValueError(f"Không phải thư mục: {source}")
        files = self.files.discover(source, recursive)
        if not files:
            print("⚠️ Không tìm thấy file .txt, .srt hoặc .vtt.")
            return

        success = failed = skipped = 0
        required_files = self.output.required_files(formats)
        progress = self.progress_factory(len(files), "Batch")
        try:
            for index, file_path in enumerate(files):
                project_number = start + index
                progress.update(index, file_path.name)
                try:
                    text = self.inputs.resolve_file(file_path).text
                    folder = output_root / f"{project_number:03d}"
                    complete = all((folder / name).exists() for name in required_files)
                    if skip_existing and complete:
                        print(f"  ⏭️ Skip {folder}")
                        skipped += 1
                        progress.update(index + 1, file_path.name)
                        continue
                    await self.synthesis.execute(
                        text=text, output_root=output_root, subtitle_mode=subtitle_mode,
                        max_words=max_words, start=start, overwrite=True, dry_run=dry_run,
                        project_number=project_number, formats=formats,
                    )
                    success += 1
                except Exception as exc:
                    failed += 1
                    print(f"❌ {file_path}: {exc}")
                    if not continue_on_error:
                        raise
                progress.update(index + 1, file_path.name)
        finally:
            progress.finish()
        print(f"✅ Success: {success} | ⏭️ Skipped: {skipped} | ❌ Failed: {failed}")


__all__ = ["BatchProcessUseCase"]
