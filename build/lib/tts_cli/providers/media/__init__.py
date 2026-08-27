"""Audio and video media provider adapters."""

import asyncio

from tts_cli.core.interfaces import MediaProcessor


async def get_media_processor(name: str = "ffmpeg") -> MediaProcessor:
	if name != "ffmpeg":
		raise ValueError(f"Media provider không hỗ trợ: {name}")
	try:
		process = await asyncio.create_subprocess_exec(
			"ffmpeg", "-version",
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.PIPE,
		)
	except FileNotFoundError as exc:
		raise RuntimeError("FFmpeg chưa được cài hoặc chưa có trong PATH.") from exc
	await process.communicate()
	if process.returncode:
		raise RuntimeError("Không thể chạy FFmpeg.")

	from tts_cli.providers.media.ffmpeg import FFmpegMediaProcessor

	return FFmpegMediaProcessor()


__all__ = ["get_media_processor"]
