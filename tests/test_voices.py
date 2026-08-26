import asyncio
from unittest.mock import AsyncMock

from tts_cli.services.voices import list_voices


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
    monkeypatch.setattr("tts_cli.services.voices.edge_tts.list_voices", mocked_list_voices)

    asyncio.run(list_voices(language="vi", gender="Female"))

    output = capsys.readouterr().out
    assert "vi-VN-HoaiMyNeural" in output
    assert "vi-VN-NamMinhNeural" not in output
    assert "Tổng: 1 voice" in output
    mocked_list_voices.assert_awaited_once()


def test_list_voices_reports_no_match(monkeypatch, capsys):
    monkeypatch.setattr(
        "tts_cli.services.voices.edge_tts.list_voices",
        AsyncMock(return_value=[]),
    )

    asyncio.run(list_voices(search="missing"))

    assert "Không tìm thấy voice." in capsys.readouterr().out