from pathlib import Path
from typing import Protocol

from tts_cli.core.models import SubtitleCue


class TTSEngine(Protocol):
    async def synthesize(self, text: str, audio_path: Path) -> list[SubtitleCue]:
        ...