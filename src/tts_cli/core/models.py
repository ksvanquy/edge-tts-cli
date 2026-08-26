from dataclasses import dataclass
from typing import Optional


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
class SubtitleCue:
    start: int
    end: int
    text: str
