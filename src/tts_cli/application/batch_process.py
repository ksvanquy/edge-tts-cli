from pathlib import Path

from tts_cli.application.synthesize import SynthesizeUseCase
from tts_cli.console.progress import ProgressBar
from tts_cli.input.resolver import InputResolver
from tts_cli.output.resolver import OutputResolver


def find_input_files(directory: Path, recursive: bool) -> list[Path]:
    iterator = directory.rglob("*") if recursive else directory.glob("*")
    extensions = {".txt", ".srt", ".vtt"}
    return sorted(
        (path for path in iterator if path.is_file() and path.suffix.lower() in extensions),
        key=lambda path: str(path).lower(),
    )


class BatchProcessUseCase:
    """Discover input files and orchestrate batch synthesis."""

    def __init__(self, synthesis: SynthesizeUseCase):
        self.synthesis = synthesis

    async def execute(
        self, source: Path, output_root: Path, recursive: bool, subtitle_mode: str,
        max_words: int, start: int, skip_existing: bool, continue_on_error: bool,
        dry_run: bool, formats: str | list[str] | None = None,
    ) -> None:
        if not source.exists():
            raise FileNotFoundError(f"Không tìm thấy thư mục: {source}")
        if not source.is_dir():
            raise ValueError(f"Không phải thư mục: {source}")
        files = find_input_files(source, recursive)
        if not files:
            print("⚠️ Không tìm thấy file .txt, .srt hoặc .vtt.")
            return

        success = failed = skipped = 0
        output_resolver = OutputResolver()
        input_resolver = InputResolver()
        required_files = output_resolver.required_files(formats)
        progress = ProgressBar(len(files), "Batch")
        for index, file_path in enumerate(files):
            project_number = start + index
            progress.update(index, file_path.name)
            try:
                text = input_resolver.resolve_file(file_path).text
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
                    progress.finish()
                    raise
            progress.update(index + 1, file_path.name)
        progress.finish()
        print(f"✅ Success: {success} | ⏭️ Skipped: {skipped} | ❌ Failed: {failed}")


__all__ = ["BatchProcessUseCase", "find_input_files"]
