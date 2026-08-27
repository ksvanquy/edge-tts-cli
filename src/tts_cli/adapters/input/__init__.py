"""Text and media input adapters."""

from tts_cli.adapters.input.media import is_audio_file, is_video_file
from tts_cli.adapters.input.resolver import InputResolver, ResolvedInput

__all__ = ["InputResolver", "ResolvedInput", "is_audio_file", "is_video_file"]
