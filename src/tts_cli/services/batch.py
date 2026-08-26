from pathlib import Path

from tts_cli.services.tts import TTSService
from tts_cli.text.resolver import InputResolver


def find_input_files(directory: Path, recursive: bool) -> list[Path]:
    iterator = directory.rglob("*") if recursive else directory.glob("*")
    extensions = {".txt", ".srt", ".vtt"}
    return sorted(
        (path for path in iterator if path.is_file() and path.suffix.lower() in extensions),
        key=lambda path: str(path).lower(),
    )


class BatchService:
    """Owns file discovery, stable numbering, and batch-level error policy."""

    def __init__(self, tts_service: TTSService):
        self.tts_service = tts_service

    async def process(
        self,
        source: Path,
        output_root: Path,
        recursive: bool,
        subtitle_mode: str,
        max_words: int,
        start: int,
        skip_existing: bool,
        continue_on_error: bool,
        dry_run: bool,
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
        for index, file_path in enumerate(files):
            project_number = start + index
            try:
                text = InputResolver().resolve_file(file_path).text
                folder = output_root / f"{project_number:03d}"
                complete = all((folder / name).exists() for name in ("audio.mp3", "subtitle.srt"))
                if skip_existing and complete:
                    print(f"  ⏭️ Skip {folder}")
                    skipped += 1
                    continue
                await self.tts_service.generate(
                    text=text,
                    output_root=output_root,
                    subtitle_mode=subtitle_mode,
                    max_words=max_words,
                    start=start,
                    overwrite=True,
                    dry_run=dry_run,
                    project_number=project_number,
                )
                success += 1
            except Exception as exc:
                failed += 1
                print(f"❌ {file_path}: {exc}")
                if not continue_on_error:
                    raise
        print(f"✅ Success: {success} | ⏭️ Skipped: {skipped} | ❌ Failed: {failed}")
