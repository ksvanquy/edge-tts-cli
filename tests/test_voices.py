import asyncio
from unittest.mock import AsyncMock

from tts_cli.services.voice_catalog import VoiceCatalogService


def test_list_voices_filters_and_sorts_results(monkeypatch, capsys):
    voices = [
        {
            "ShortName": "en-US-ZaraNeural",
            "Locale": "en-US",
            "Gender": "Female",
            "FriendlyName": "Zara",
        },
        {
            "ShortName": "vi-VN-NamMinhNeural",
            "Locale": "vi-VN",
            "Gender": "Male",
            "FriendlyName": "Nam Minh",
        },
        {
            "ShortName": "vi-VN-HoaiMyNeural",
            "Locale": "vi-VN",
            "Gender": "Female",
            "FriendlyName": "Hoai My",
        },
    ]
    mocked_list_voices = AsyncMock(return_value=voices)

    result = asyncio.run(VoiceCatalogService(mocked_list_voices).find(language="vi", gender="Female"))

    assert [voice["ShortName"] for voice in result] == ["vi-VN-HoaiMyNeural"]
    mocked_list_voices.assert_awaited_once()


def test_list_voices_reports_no_match(monkeypatch, capsys):
    loader = AsyncMock(return_value=[])

    result = asyncio.run(VoiceCatalogService(loader).find(search="missing"))

    assert result == []