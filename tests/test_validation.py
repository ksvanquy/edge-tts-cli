from types import SimpleNamespace

import pytest

from tts_cli.core.config import normalize_pitch, normalize_rate, validate_args, validate_pitch, validate_rate


def test_validate_args_accepts_defaults():
    validate_args(SimpleNamespace(rate="+0%", pitch="+0Hz", volume="+0%", retries=3, timeout=60.0, max_words=8, start=1, overwrite=False, skip_existing=False))


def test_validate_pitch_rejects_invalid_value():
    with pytest.raises(ValueError):
        validate_pitch("wrong")


@pytest.mark.parametrize("value", ["+0%", "+10%", "-25%", "+100%"])
def test_validate_rate_accepts_signed_percentages(value):
    validate_rate(value)


@pytest.mark.parametrize(("value", "expected"), [("0", "+0%"), ("10%", "+10%"), ("-10", "-10%")])
def test_normalize_rate_accepts_conventional_values(value, expected):
    assert normalize_rate(value) == expected


@pytest.mark.parametrize("value", ["fast", "+1.5%", "10 percent", ""])
def test_validate_rate_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        validate_rate(value)


@pytest.mark.parametrize("value", ["+0Hz", "-5Hz", "+12hz", "-100HZ"])
def test_validate_pitch_accepts_signed_hertz(value):
    validate_pitch(value)


@pytest.mark.parametrize(("value", "expected"), [("0", "+0Hz"), ("2Hz", "+2Hz"), ("-2", "-2Hz")])
def test_normalize_pitch_accepts_conventional_values(value, expected):
    assert normalize_pitch(value) == expected


@pytest.mark.parametrize("value", ["slow", "+1.5Hz", "2 hertz", ""])
def test_validate_pitch_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        validate_pitch(value)
