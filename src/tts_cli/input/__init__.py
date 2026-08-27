"""Input sources and readers."""

from tts_cli.input.processor import normalize_text
from tts_cli.input.readers import InputReader, SrtInputReader, TxtInputReader, VttInputReader
from tts_cli.input.resolver import InputResolver, ResolvedInput

__all__ = [
    "InputReader",
    "InputResolver",
    "ResolvedInput",
    "SrtInputReader",
    "TxtInputReader",
    "VttInputReader",
    "normalize_text",
]
