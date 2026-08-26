from types import SimpleNamespace

import pytest

from tts_cli.core.config import validate_args, validate_pitch


def test_validate_args_accepts_defaults():
    validate_args(SimpleNamespace(rate="+0%", pitch="+0Hz", volume="+0%", retries=3, timeout=60.0, max_words=8, start=1, overwrite=False, skip_existing=False))


def test_validate_pitch_rejects_invalid_value():
    with pytest.raises(ValueError):
        validate_pitch("wrong")
