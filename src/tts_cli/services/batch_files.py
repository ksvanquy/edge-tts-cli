from pathlib import Path


class BatchFileService:
    supported_extensions = frozenset({".txt", ".srt", ".vtt"})

    def discover(self, directory: Path, recursive: bool) -> list[Path]:
        iterator = directory.rglob("*") if recursive else directory.glob("*")
        return sorted(
            (path for path in iterator if path.is_file() and path.suffix.lower() in self.supported_extensions),
            key=lambda path: str(path).lower(),
        )
