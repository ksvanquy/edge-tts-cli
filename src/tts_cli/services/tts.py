import asyncio
from pathlib import Path

import edge_tts

from tts_cli.console.printer import print_warning
from tts_cli.core.models import SubtitleCue, TTSConfig
from tts_cli.output.project import get_next_number
from tts_cli.subtitle.cues import build_subtitle_cues
from tts_cli.subtitle.srt import cues_to_srt, format_duration
from tts_cli.text.processor import normalize_text


class TTSService:
    """Owns Edge TTS synthesis and project artifact generation."""

    def __init__(self, config: TTSConfig):
        self.config = config

    async def synthesize_once(self, text: str, audio_path: Path) -> list[SubtitleCue]:
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.config.voice,
            rate=self.config.rate,
            pitch=self.config.pitch,
            volume=self.config.volume,
            boundary="WordBoundary",
            proxy=self.config.proxy,
            connect_timeout=int(self.config.timeout),
            receive_timeout=int(self.config.timeout),
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
        return word_cues

    async def synthesize_with_retry(self, text: str, audio_path: Path) -> list[SubtitleCue]:
        total_attempts = self.config.retries + 1
        last_error = None
        for attempt in range(1, total_attempts + 1):
            print(f"  🎙️ TTS {attempt}/{total_attempts}")
            try:
                return await asyncio.wait_for(self.synthesize_once(text, audio_path), timeout=self.config.timeout)
            except Exception as exc:
                last_error = exc
                if audio_path.exists():
                    try:
                        audio_path.unlink()
                    except OSError as unlink_error:
                        print_warning(f"Không thể xóa audio lỗi: {unlink_error}")
                if attempt < total_attempts:
                    wait_seconds = min(2 ** (attempt - 1), 10)
                    print_warning(f"TTS lỗi: {exc}")
                    print(f"  🔄 Retry sau {wait_seconds}s...")
                    await asyncio.sleep(wait_seconds)
        raise RuntimeError(f"Không thể tạo audio sau {total_attempts} lần thử: {last_error}")

    async def generate(
        self,
        text: str,
        output_root: Path,
        subtitle_mode: str,
        max_words: int,
        start: int = 1,
        overwrite: bool = False,
        dry_run: bool = False,
        project_number: int | None = None,
    ) -> int:
        text = normalize_text(text)
        if not text:
            raise ValueError("Text rỗng.")
        output_root.mkdir(parents=True, exist_ok=True)
        number = project_number if project_number is not None else get_next_number(output_root, start)
        folder = output_root / f"{number:03d}"
        audio_path = folder / "audio.mp3"
        subtitle_path = folder / "subtitle.srt"
        if dry_run:
            print(f"  → {folder}/")
            print("     ├── audio.mp3")
            print("     └── subtitle.srt")
            return number
        if folder.exists() and not overwrite:
            raise FileExistsError(f"Folder output đã tồn tại: {folder}")
        folder.mkdir(parents=True, exist_ok=True)
        word_cues = await self.synthesize_with_retry(text, audio_path)
        subtitle_cues = build_subtitle_cues(word_cues, subtitle_mode, max_words)
        subtitle_path.write_text(cues_to_srt(subtitle_cues), encoding="utf-8", newline="\n")
        duration = format_duration(word_cues[-1].end) if word_cues else "0.00s"
        print(f"✅ PROJECT {number:03d}: {len(word_cues)} từ, {len(subtitle_cues)} cues, {duration}")
        return number
