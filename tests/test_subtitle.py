from tts_cli.core.models import SubtitleCue
from tts_cli.subtitle.cues import build_subtitle_cues
from tts_cli.subtitle.srt import cues_to_srt, format_srt_time


def test_format_srt_time():
    assert format_srt_time(1_234_567) == "00:00:01,234"


def test_phrase_cues_group_words():
    cues = [SubtitleCue(index * 1_000_000, (index + 1) * 1_000_000, word) for index, word in enumerate(("Một", "hai", "ba"))]
    result = build_subtitle_cues(cues, "phrase", 2)
    assert [cue.text for cue in result] == ["Một hai", "ba"]
    assert cues_to_srt(result).startswith("1\n00:00:00,000 --> 00:00:02,000\nMột hai")
