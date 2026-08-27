"""Helpers for reading common media metadata from FFprobe output."""

from dataclasses import dataclass
from pathlib import Path

from tts_cli.providers.media.ffmpeg import FFmpegMediaProcessor


@dataclass(frozen=True)
class MediaMetadata:
    duration: float
    codec: str
    sample_rate: int
    channels: int
    bitrate: int


async def probe_all(media_path: Path) -> MediaMetadata:
    data = await FFmpegMediaProcessor().probe(media_path)
    format_data = data.get("format", {})
    streams = data.get("streams", [])
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    return MediaMetadata(
        duration=float(format_data.get("duration", 0) or 0),
        codec=str(audio.get("codec_name", "unknown")),
        sample_rate=int(audio.get("sample_rate", 0) or 0),
        channels=int(audio.get("channels", 0) or 0),
        bitrate=int(format_data.get("bit_rate", 0) or 0),
    )


async def probe_duration(media_path: Path) -> float:
    return (await probe_all(media_path)).duration


async def probe_codec(media_path: Path) -> str:
    return (await probe_all(media_path)).codec


async def probe_sample_rate(media_path: Path) -> int:
    return (await probe_all(media_path)).sample_rate


__all__ = ["MediaMetadata", "probe_all", "probe_codec", "probe_duration", "probe_sample_rate"]