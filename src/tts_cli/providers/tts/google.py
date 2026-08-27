"""Google Cloud Text-to-Speech provider."""

import asyncio
import re
from pathlib import Path

from tts_cli.core.models import ProviderCapabilities, SynthesisResult, TTSConfig


class GoogleTTSEngine:
    """Synthesize MP3 through Google Cloud TTS."""

    capabilities = ProviderCapabilities(voice_listing=True)

    def __init__(self, config: TTSConfig):
        self.config = config

    async def synthesize(self, text: str, audio_path: Path) -> SynthesisResult:
        try:
            from google.cloud import texttospeech
        except ImportError as exc:
            raise RuntimeError(
                "Google TTS chưa được cài. Dùng `pip install .[google]`."
            ) from exc

        await asyncio.to_thread(self._synthesize, text, audio_path, texttospeech)
        return SynthesisResult(audio_path, [], {"provider": "google", "word_timing": False})

    def _synthesize(self, text: str, audio_path: Path, texttospeech) -> None:
        client = texttospeech.TextToSpeechClient()
        voice_name = self.config.voice
        voice_parts = voice_name.split("-")
        language_code = "-".join(voice_parts[:2]) if len(voice_parts) >= 2 else "en-US"
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=text),
            voice=texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name,
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=self._rate(self.config.rate),
                pitch=self._number(self.config.pitch, "Hz"),
            ),
        )
        audio_path.write_bytes(response.audio_content)

    @staticmethod
    def _number(value: str, suffix: str) -> float:
        pattern = r"([+-]?\d+(?:\.\d+)?)(?:" + re.escape(suffix) + r")?"
        match = re.fullmatch(pattern, value.strip(), re.IGNORECASE)
        return float(match.group(1)) if match else 0.0

    @classmethod
    def _rate(cls, value: str) -> float:
        return 1.0 + cls._number(value, "%") / 100.0