from tts_cli.core.models import SubtitleCue


def format_srt_time(microseconds: int) -> str:
    total_ms = max(0, microseconds // 1000)
    hours, total_ms = divmod(total_ms, 3_600_000)
    minutes, total_ms = divmod(total_ms, 60_000)
    seconds, milliseconds = divmod(total_ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def format_duration(microseconds: int) -> str:
    return f"{microseconds / 1_000_000:.2f}s"


def cues_to_srt(cues: list[SubtitleCue]) -> str:
    blocks = []
    for index, cue in enumerate(cues, start=1):
        blocks.append(
            f"{index}\n{format_srt_time(cue.start)} --> {format_srt_time(cue.end)}\n{cue.text.strip()}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")
