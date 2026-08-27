import asyncio
import json
from pathlib import Path


class FFmpegMediaProcessor:
    """FFmpeg adapter for extracting audio and probing media metadata."""

    async def extract_audio(self, source: Path, destination: Path) -> None:
        process = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-i", str(source), "-vn", "-acodec", "pcm_s16le", str(destination),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode:
            raise RuntimeError(f"FFmpeg không thể tách audio: {stderr.decode(errors='replace').strip()}")

    async def probe(self, source: Path) -> dict[str, object]:
        process = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(source),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode:
            raise RuntimeError(f"FFprobe không thể đọc media: {stderr.decode(errors='replace').strip()}")
        return json.loads(stdout)
