from pathlib import Path
from types import SimpleNamespace

import pytest

from tts_cli.text.processor import normalize_text
from tts_cli.text.resolver import InputResolver


def test_normalize_text_removes_bom_and_empty_lines():
    assert normalize_text("\ufeff  Xin chào  \r\n\r\n mọi người ") == "Xin chào\nmọi người"


def test_normalize_text_handles_empty_input_and_old_mac_newlines():
    assert normalize_text("") == ""
    assert normalize_text("  Một\rHai\n\n Ba ") == "Một\nHai\nBa"


def test_read_txt_file_reads_utf8_sig(tmp_path: Path):
    path = tmp_path / "script.txt"
    path.write_text("\ufeffXin chào", encoding="utf-8")
    assert InputResolver().resolve_file(path).text == "Xin chào"


def test_read_input_file_extracts_srt_dialogue(tmp_path: Path):
    path = tmp_path / "script.srt"
    path.write_text(
        "cue-a\n00:00:00,000 --> 00:00:01,000\nXin chào\n"
        "\n2\n00:00:01,000 --> 00:00:02,000\n"
        "mọi người\nđây là dòng thứ hai.\n",
        encoding="utf-8",
    )
    assert InputResolver().resolve_file(path).text == "Xin chào mọi người đây là dòng thứ hai."


def test_read_srt_does_not_drop_numeric_dialogue(tmp_path: Path):
    path = tmp_path / "numeric.srt"
    path.write_text("1\n00:00:00,000 --> 00:00:01,000\n2026\n", encoding="utf-8")

    assert InputResolver().resolve_file(path).text == "2026"


def test_read_input_file_extracts_vtt_dialogue_and_skips_notes(tmp_path: Path):
    path = tmp_path / "script.vtt"
    path.write_text(
        "WEBVTT\n\nNOTE\nmetadata\n\n00:00:00.000 --> 00:00:01.000\n"
        "Xin chào\n\n00:00:01.000 --> 00:00:02.000\n"
        "mọi người.\n",
        encoding="utf-8",
    )
    assert InputResolver().resolve_file(path).text == "Xin chào mọi người."


def test_resolve_text_argument_normalizes_text():
    args = SimpleNamespace(text="  Xin chào\r\n\r\n mọi người  ", file=None)

    resolved = InputResolver().resolve(args)

    assert resolved.text == "Xin chào\nmọi người"
    assert resolved.source is None
    assert resolved.format == "text"


def test_resolve_file_rejects_unsupported_extension(tmp_path: Path):
    path = tmp_path / "script.docx"
    path.write_text("text", encoding="utf-8")

    with pytest.raises(ValueError, match="không được hỗ trợ"):
        InputResolver().resolve_file(path)
