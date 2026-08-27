from pathlib import Path

from tts_cli.__main__ import error_hint
from tts_cli.core.errors import RetryExhaustedError


def test_error_hint_explains_common_cli_failures():
    assert "đường dẫn" in error_hint(FileNotFoundError("missing"))
    assert "--overwrite" in error_hint(FileExistsError("exists"))
    assert "UTF-8" in error_hint(UnicodeDecodeError("utf-8", b"x", 0, 1, "bad"))


def test_error_hint_returns_none_for_unexpected_error():
    assert error_hint(RuntimeError("unexpected")) is None


def test_error_hint_uses_retry_cause():
    assert "--timeout" in error_hint(RetryExhaustedError(2, TimeoutError("slow")))
    assert "kết nối" in error_hint(RetryExhaustedError(2, ConnectionError("offline")))