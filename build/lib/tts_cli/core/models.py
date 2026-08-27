from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class TTSConfig:
    voice: str
    rate: str
    pitch: str
    volume: str
    retries: int
    timeout: float
    proxy: Optional[str]


@dataclass
class TranscribeConfig:
    model_size: str = "base"
    language: str | None = None
    device: str = "auto"
    compute_type: str = "auto"


@dataclass
class SubtitleCue:
    start: int
    end: int
    text: str


@dataclass
class SynthesisResult:
    audio_path: Path
    word_cues: list[SubtitleCue]
    metadata: dict[str, Any] | None = None


@dataclass
class TranscriptResult:
    cues: list[SubtitleCue]
    language: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class OutputContext:
    folder: Path
    word_cues: list[SubtitleCue]
    subtitle_cues: list[SubtitleCue]
    audio_path: Path


@dataclass(frozen=True)
class ProviderCapabilities:
    word_timing: bool = False
    sentence_timing: bool = False
    streaming: bool = False
    voice_listing: bool = False
