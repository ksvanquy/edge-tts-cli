from pathlib import Path

from tts_cli.text.processor import normalize_text, read_input_file, read_txt_file


def test_normalize_text_removes_bom_and_empty_lines():
    assert normalize_text("\ufeff  Xin chào  \r\n\r\n mọi người ") == "Xin chào\nmọi người"


def test_read_txt_file_reads_utf8_sig(tmp_path: Path):
    path = tmp_path / "script.txt"
    path.write_text("\ufeffXin chào", encoding="utf-8")
    assert read_txt_file(path) == "Xin chào"


def test_read_input_file_extracts_srt_dialogue(tmp_path: Path):
    path = tmp_path / "script.srt"
    path.write_text(
        "cue-a\n00:00:00,000 --> 00:00:01,000\nXin chào\n"
        "\n2\n00:00:01,000 --> 00:00:02,000\n"
        "mọi người\nđây là dòng thứ hai.\n",
        encoding="utf-8",
    )
    assert read_input_file(path) == "Xin chào mọi người đây là dòng thứ hai."


def test_read_input_file_extracts_vtt_dialogue_and_skips_notes(tmp_path: Path):
    path = tmp_path / "script.vtt"
    path.write_text(
        "WEBVTT\n\nNOTE\nmetadata\n\n00:00:00.000 --> 00:00:01.000\n"
        "Xin chào\n\n00:00:01.000 --> 00:00:02.000\n"
        "mọi người.\n",
        encoding="utf-8",
    )
    assert read_input_file(path) == "Xin chào mọi người."
