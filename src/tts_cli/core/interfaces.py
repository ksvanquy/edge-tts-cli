from pathlib import Path
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from tts_cli.core.models import OutputContext, ProviderCapabilities, SynthesisResult, TranscriptResult


class TTSEngine(Protocol):
    capabilities: ProviderCapabilities

    async def synthesize(self, text: str, audio_path: Path) -> SynthesisResult:
        ...


class SpeechTranscriber(Protocol):
    name: str

    async def transcribe(self, audio_path: Path) -> TranscriptResult:
        ...


class MediaProcessor(Protocol):
    async def extract_audio(self, source: Path, destination: Path) -> None:
        ...

    async def probe(self, source: Path) -> dict[str, object]:
        ...


class RetryPort(Protocol):
    async def execute(
        self,
        operation: Callable[[], Awaitable[Any]],
        retries: int,
        timeout: float,
        cleanup_path: Path | None = None,
    ) -> Any:
        ...


class ProjectPort(Protocol):
    def paths(self, output_root: Path, start: int = 1, number: int | None = None) -> Any:
        ...


class OutputFormatPort(Protocol):
    extension: str

    def write(self, context: OutputContext) -> Path:
        ...


class OutputPort(Protocol):
    def resolve(self, formats: str | list[str] | None) -> list[OutputFormatPort]:
        ...

    @staticmethod
    def filename(handler: OutputFormatPort) -> str:
        ...

    def required_files(self, formats: str | list[str] | None) -> set[str]:
        ...

    def write(self, context: Any, formats: str | list[str] | None) -> list[Path]:
        ...

    def cleanup(self, folder: Path, formats: str | list[str] | None, remove_folder: bool = False) -> None:
        ...


class InputPort(Protocol):
    def resolve_file(self, path: Path) -> Any:
        ...


class BatchFilesPort(Protocol):
    def discover(self, directory: Path, recursive: bool) -> list[Path]:
        ...


class ProgressPort(Protocol):
    enabled: bool

    def update(self, current: int, detail: str = "") -> None:
        ...

    def finish(self) -> None:
        ...


class TranscriptionPort(Protocol):
    async def execute(self, source: Path) -> TranscriptResult:
        ...


class VoiceCatalogPort(Protocol):
    async def find(
        self,
        language: str | None = None,
        gender: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        ...


__all__ = [
    "BatchFilesPort", "InputPort", "MediaProcessor", "OutputPort", "ProgressPort",
    "ProjectPort", "RetryPort", "SpeechTranscriber", "TTSEngine",
    "TranscriptionPort", "VoiceCatalogPort",
]
