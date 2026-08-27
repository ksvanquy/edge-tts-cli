import re
from abc import ABC, abstractmethod
from pathlib import Path

from tts_cli.text.processor import normalize_text


TIMESTAMP_LINE = re.compile(
    r"^(?:\d{2}:)?\d{2}:\d{2}[,.]\d{3}\s+-->(?:\s+|\S)(?:\d{2}:)?\d{2}:\d{2}[,.]\d{3}"
)


class InputReader(ABC):
    @abstractmethod
    def read(self, path: Path) -> str:
        pass

    @staticmethod
    def read_utf8(path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {path}")
        if not path.is_file():
            raise ValueError(f"Đường dẫn không phải file: {path}")
        try:
            return path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError(f"File không phải UTF-8: {path}") from exc


class TxtInputReader(InputReader):
    def read(self, path: Path) -> str:
        return normalize_text(self.read_utf8(path))


class SubtitleInputReader(InputReader):
    def read(self, path: Path) -> str:
        lines = self.read_utf8(path).replace("\r\n", "\n").replace("\r", "\n").split("\n")
        result = []
        skip_metadata = False
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped in {"WEBVTT", "STYLE", "REGION"}:
                skip_metadata = stripped != "WEBVTT"
                continue
            if stripped == "NOTE":
                skip_metadata = True
                continue
            if skip_metadata:
                if not stripped:
                    skip_metadata = False
                continue
            next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
            if (
                not stripped
                or TIMESTAMP_LINE.match(stripped)
                or TIMESTAMP_LINE.match(next_line)
                or (stripped.isdigit() and TIMESTAMP_LINE.match(next_line))
            ):
                continue
            result.append(stripped)
        return " ".join(result)


class SrtInputReader(SubtitleInputReader):
    pass


class VttInputReader(SubtitleInputReader):
    pass