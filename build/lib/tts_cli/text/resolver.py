import sys
from dataclasses import dataclass
from pathlib import Path

from tts_cli.text.readers import InputReader, SrtInputReader, TxtInputReader, VttInputReader
from tts_cli.text.processor import normalize_text


@dataclass(frozen=True)
class ResolvedInput:
    text: str
    source: Path | None = None
    format: str = "text"


class InputResolver:
    def __init__(self, readers: dict[str, InputReader] | None = None):
        self.readers = readers or {
            ".txt": TxtInputReader(),
            ".srt": SrtInputReader(),
            ".vtt": VttInputReader(),
        }

    def resolve(self, args) -> ResolvedInput:
        if args.text is not None:
            return ResolvedInput(normalize_text(args.text))
        if args.file:
            return self.resolve_file(Path(args.file))
        if not sys.stdin.isatty():
            text = normalize_text(sys.stdin.read())
            if not text:
                raise ValueError("stdin không chứa text.")
            return ResolvedInput(text)
        raise ValueError("Chưa cung cấp input.\nDùng -t/--text hoặc -f/--file.")

    def resolve_file(self, path: Path) -> ResolvedInput:
        extension = path.suffix.lower()
        reader = self.readers.get(extension)
        if reader is None:
            supported = ", ".join(sorted(self.readers))
            raise ValueError(f"Định dạng không được hỗ trợ: {path.suffix}. Chỉ nhận: {supported}")
        text = reader.read(path)
        if not text:
            raise ValueError(f"File input rỗng hoặc không có lời thoại: {path}")
        return ResolvedInput(text, path, extension[1:])