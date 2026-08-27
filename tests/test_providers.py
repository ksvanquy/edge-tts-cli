import asyncio
from pathlib import Path

import pytest

from tts_cli.core.models import TTSConfig
from tts_cli.providers.tts.factory import TTSProviderFactory
from tts_cli.providers.tts.google import GoogleTTSEngine


def make_config() -> TTSConfig:
    return TTSConfig("en-US-Neural2-A", "+0%", "+0Hz", "+0%", 0, 1.0, None)


def test_factory_creates_registered_google_provider():
    provider = TTSProviderFactory.create(" GOOGLE ", make_config())

    assert isinstance(provider, GoogleTTSEngine)


def test_google_provider_requires_optional_dependency(tmp_path: Path, monkeypatch):
    real_import = __import__("builtins").__import__

    def block_google(name, *args, **kwargs):
        if name == "google.cloud" or name.startswith("google.cloud."):
            raise ImportError("blocked for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", block_google)

    with pytest.raises(RuntimeError, match=r"pip install \.\[google\]"):
        asyncio.run(GoogleTTSEngine(make_config()).synthesize("Xin", tmp_path / "audio.mp3"))


def test_google_provider_maps_edge_style_rate_and_pitch():
    assert GoogleTTSEngine._rate("+20%") == pytest.approx(1.2)
    assert GoogleTTSEngine._number("-2Hz", "Hz") == pytest.approx(-2)