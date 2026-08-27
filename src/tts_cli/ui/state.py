from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Literal

from tts_cli.cli.constants import DEFAULT_MAX_WORDS, DEFAULT_OUTPUT, DEFAULT_SUBTITLE_MODE
from tts_cli.core.constants import DEFAULT_PITCH, DEFAULT_RATE, DEFAULT_RETRIES, DEFAULT_TIMEOUT, DEFAULT_VOICE, DEFAULT_VOLUME
from tts_cli.core.errors import RetryExhaustedError


Mode = Literal["generate", "batch", "transcribe", "voices"]
TaskStatus = Literal["Idle", "Running", "Succeeded", "Failed", "Cancelled"]


@dataclass
class AppState:
    active_mode: Mode = "generate"
    status: TaskStatus = "Idle"
    message: str = "Sẵn sàng"
    error_message: str | None = None
    result_summary: str = "Chưa có kết quả"
    last_result: Any = None
    notifications: list[str] = field(default_factory=list)
    generate_values: dict[str, Any] = field(default_factory=lambda: {
        "engine": "edge", "voice": DEFAULT_VOICE, "rate": DEFAULT_RATE,
        "pitch": DEFAULT_PITCH, "volume": DEFAULT_VOLUME, "subtitle_mode": DEFAULT_SUBTITLE_MODE,
        "max_words": DEFAULT_MAX_WORDS, "output": DEFAULT_OUTPUT, "formats": "mp3,srt",
        "retries": DEFAULT_RETRIES, "timeout": DEFAULT_TIMEOUT, "proxy": None,
        "text": "", "file": "",
    })
    batch_values: dict[str, Any] = field(default_factory=lambda: {
        "engine": "edge", "voice": DEFAULT_VOICE, "rate": DEFAULT_RATE, "pitch": DEFAULT_PITCH,
        "volume": DEFAULT_VOLUME, "subtitle_mode": DEFAULT_SUBTITLE_MODE, "max_words": DEFAULT_MAX_WORDS,
        "output": DEFAULT_OUTPUT, "formats": "mp3,srt", "retries": DEFAULT_RETRIES,
        "timeout": DEFAULT_TIMEOUT, "proxy": None, "directory": "", "recursive": False,
        "skip_existing": False, "continue_on_error": False, "dry_run": False,
    })
    transcribe_values: dict[str, Any] = field(default_factory=lambda: {
        "source": "", "output": "subtitle.srt", "model_size": "base", "language": "", "device": "auto",
    })
    voices_values: dict[str, Any] = field(default_factory=lambda: {
        "engine": "edge", "language": "", "gender": "", "search": "",
    })

    def save_to_file(self, filepath: str | Path = "config.json") -> None:
        """Lưu toàn bộ state cấu hình hiện tại ra file JSON."""
        try:
            data = {
                "generate_values": self.generate_values,
                "batch_values": self.batch_values,
                "transcribe_values": self.transcribe_values,
                "voices_values": self.voices_values,
            }
            Path(filepath).write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
        except Exception as e:
            print(f"Không thể lưu state: {e}")

    @classmethod
    def load_from_file(cls, filepath: str | Path = "config.json") -> "AppState":
        """Khởi tạo AppState và nạp dữ liệu cũ từ file JSON nếu có."""
        instance = cls()
        path = Path(filepath)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if "generate_values" in data:
                    instance.generate_values.update(data["generate_values"])
                if "batch_values" in data:
                    instance.batch_values.update(data["batch_values"])
                if "transcribe_values" in data:
                    instance.transcribe_values.update(data["transcribe_values"])
                if "voices_values" in data:
                    instance.voices_values.update(data["voices_values"])
            except Exception as e:
                print(f"Lỗi đọc state từ file: {e}")
        return instance

    def start(self) -> None:
        self.status = "Running"
        self.error_message = None
        self.message = "Đang xử lý..."
        self.result_summary = "Đang xử lý..."

    def succeed(self, message: str, result: Any = None) -> None:
        self.status = "Succeeded"
        self.message = message
        self.result_summary = message
        self.last_result = result

    def fail(self, error: Exception) -> None:
        self.status = "Failed"
        if isinstance(error, RetryExhaustedError):
            cause = error.cause
            cause_message = _exception_message(cause)
            self.error_message = f"{error.attempts} lần thử thất bại: {cause_message}"
        else:
            self.error_message = _exception_message(error)
        self.message = "Tác vụ thất bại"
        self.result_summary = "Tác vụ thất bại"


def _exception_message(error: Exception | None) -> str:
    if error is None:
        return "Không xác định"
    message = str(error).strip()
    if not message or message.lower() == "none":
        return error.__class__.__name__
    return message