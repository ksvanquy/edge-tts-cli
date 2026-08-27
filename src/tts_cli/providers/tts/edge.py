"""Edge TTS provider."""

from pathlib import Path

import edge_tts

from tts_cli.adapters.console.printer import print_warning
from tts_cli.core.models import ProviderCapabilities, SynthesisResult, SubtitleCue, TTSConfig


class EdgeTTSEngine:
	capabilities = ProviderCapabilities(word_timing=True, sentence_timing=True, voice_listing=True)

	def __init__(self, config: TTSConfig):
		self.config = config

	async def synthesize(self, text: str, audio_path: Path) -> SynthesisResult:
		communicate = edge_tts.Communicate(
			text=text, voice=self.config.voice, rate=self.config.rate,
			pitch=self.config.pitch, volume=self.config.volume,
			boundary="WordBoundary", proxy=self.config.proxy,
			connect_timeout=int(self.config.timeout), receive_timeout=int(self.config.timeout),
		)
		word_cues = []
		with audio_path.open("wb") as audio_file:
			async for chunk in communicate.stream():
				if chunk.get("type") == "audio":
					audio_data = chunk.get("data")
					if isinstance(audio_data, bytes):
						audio_file.write(audio_data)
				elif chunk.get("type") == "WordBoundary":
					try:
						offset = int(chunk.get("offset", 0))
						duration = int(chunk.get("duration", 0))
						word = str(chunk.get("text", ""))
					except (TypeError, ValueError) as exc:
						print_warning(f"Bỏ qua WordBoundary không hợp lệ: {exc}")
						continue
					if word.strip() and offset >= 0 and duration >= 0:
						word_cues.append(SubtitleCue(offset // 10, (offset + duration) // 10, word))
		return SynthesisResult(audio_path, word_cues, {"provider": "edge"})


__all__ = ["EdgeTTSEngine"]
