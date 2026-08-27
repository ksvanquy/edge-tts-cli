"""Media input classification and processor construction."""

import asyncio
from pathlib import Path

from tts_cli.core.interfaces import MediaProcessor

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".flv", ".wmv", ".m4v"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac", ".wma"}


def is_video_file(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def is_audio_file(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_EXTENSIONS


async def get_media_processor() -> MediaProcessor:
    try:
        process = await asyncio.create_subprocess_exec(
            "ffmpeg", "-version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
    except FileNotFoundError as exc:
        raise RuntimeError("FFmpeg chưa được cài hoặc chưa có trong PATH.") from exc
    await process.communicate()
    if process.returncode:
        raise RuntimeError("Không thể chạy FFmpeg.")
    from tts_cli.providers.media.ffmpeg import FFmpegMediaProcessor

    return FFmpegMediaProcessor()


__all__ = ["get_media_processor", "is_audio_file", "is_video_file"]