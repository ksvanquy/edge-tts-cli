import json

from tts_cli.core.models import SubtitleCue
from tts_cli.output.formats import OutputContext
from tts_cli.output.project import create_output_folder, get_next_number
from tts_cli.output.resolver import OutputResolver


def test_next_number_and_folder_format(tmp_path):
    create_output_folder(tmp_path, 1)
    (tmp_path / "005").mkdir()
    assert get_next_number(tmp_path) == 6


def test_output_resolver_writes_requested_formats(tmp_path):
    folder = tmp_path / "001"
    folder.mkdir()
    audio_path = folder / "audio.mp3"
    audio_path.write_bytes(b"audio")
    cues = [SubtitleCue(0, 1_000_000, "Xin chào")]

    OutputResolver().write(OutputContext(folder, cues, cues, audio_path), "srt,vtt,json")

    assert not audio_path.exists()
    assert (folder / "subtitle.srt").exists()
    assert (folder / "subtitle.vtt").read_text(encoding="utf-8").startswith("WEBVTT")
    payload = json.loads((folder / "subtitle.json").read_text(encoding="utf-8"))
    assert payload == [{"index": 1, "start": 0, "end": 1_000_000, "text": "Xin chào"}]


def test_output_resolver_rejects_unknown_format():
    try:
        OutputResolver().resolve("mp3,xml")
    except ValueError as exc:
        assert "xml" in str(exc)
    else:
        raise AssertionError("Expected unsupported format to be rejected")


def test_output_resolver_cleans_partial_artifacts(tmp_path):
    folder = tmp_path / "001"
    folder.mkdir()
    (folder / "audio.mp3").write_bytes(b"partial")
    (folder / "subtitle.srt").write_text("partial", encoding="utf-8")
    resolver = OutputResolver()

    resolver.cleanup(folder, "mp3,srt", remove_folder=True)

    assert not folder.exists()
