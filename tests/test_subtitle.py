from tts_cli.core.models import SubtitleCue
from tts_cli.subtitle.cues import build_subtitle_cues, make_phrase_cues, make_sentence_cues
from tts_cli.subtitle.srt import cues_to_srt, format_srt_time


def test_format_srt_time():
    assert format_srt_time(1_234_567) == "00:00:01,234"


def test_format_srt_time_clamps_negative_and_formats_long_duration():
    assert format_srt_time(-1) == "00:00:00,000"
    assert format_srt_time(3_661_001_000) == "01:01:01,001"


def test_phrase_cues_group_words():
    cues = [SubtitleCue(index * 1_000_000, (index + 1) * 1_000_000, word) for index, word in enumerate(("Một", "hai", "ba"))]
    result = build_subtitle_cues(cues, "phrase", 2)
    assert [cue.text for cue in result] == ["Một hai", "ba"]
    assert cues_to_srt(result).startswith("1\n00:00:00,000 --> 00:00:02,000\nMột hai")


def test_make_phrase_cues_preserves_boundaries_and_remainder():
    word_cues = [
        SubtitleCue(0, 100_000, "Một"),
        SubtitleCue(100_000, 200_000, "hai"),
        SubtitleCue(200_000, 300_000, "ba"),
        SubtitleCue(300_000, 400_000, "bốn"),
        SubtitleCue(400_000, 500_000, "năm"),
    ]

    result = make_phrase_cues(word_cues, 2)

    assert [(cue.start, cue.end, cue.text) for cue in result] == [
        (0, 200_000, "Một hai"),
        (200_000, 400_000, "ba bốn"),
        (400_000, 500_000, "năm"),
    ]


def test_make_sentence_cues_groups_until_sentence_punctuation():
    word_cues = [
        SubtitleCue(0, 100_000, "Đây"),
        SubtitleCue(100_000, 200_000, "là"),
        SubtitleCue(200_000, 300_000, "câu."),
        SubtitleCue(300_000, 400_000, "Câu"),
        SubtitleCue(400_000, 500_000, "sau!"),
    ]

    result = make_sentence_cues(word_cues)

    assert [(cue.start, cue.end, cue.text) for cue in result] == [
        (0, 300_000, "Đây là câu."),
        (300_000, 500_000, "Câu sau!"),
    ]
