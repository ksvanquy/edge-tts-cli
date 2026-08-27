import re
from tts_cli.core.models import SubtitleCue


def make_phrase_cues(word_cues: list[SubtitleCue], max_words: int) -> list[SubtitleCue]:
    return [
        SubtitleCue(current[0].start, current[-1].end, " ".join(item.text for item in current))
        for index in range(0, len(word_cues), max_words)
        if (current := word_cues[index:index + max_words])
    ]


def make_sentence_cues(word_cues: list[SubtitleCue]) -> list[SubtitleCue]:
    result = []
    current = []
    sentence_end = re.compile(r"[.!?…。！？]$")
    for cue in word_cues:
        current.append(cue)
        if sentence_end.search(cue.text.strip()):
            result.append(SubtitleCue(current[0].start, current[-1].end, " ".join(item.text for item in current)))
            current = []
    if current:
        result.append(SubtitleCue(current[0].start, current[-1].end, " ".join(item.text for item in current)))
    return result


def build_subtitle_cues(word_cues: list[SubtitleCue], mode: str, max_words: int) -> list[SubtitleCue]:
    if mode == "word":
        return word_cues
    if mode == "sentence":
        return make_sentence_cues(word_cues)
    if mode == "phrase":
        return make_phrase_cues(word_cues, max_words)
    raise ValueError(f"Subtitle mode không hợp lệ: {mode}")
