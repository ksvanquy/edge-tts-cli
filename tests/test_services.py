import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest

from tts_cli.core.models import SynthesisResult, SubtitleCue, TTSConfig
from tts_cli.console.progress import ProgressBar
from tts_cli.application.batch_process import BatchProcessUseCase, find_input_files
from tts_cli.application.synthesize import SynthesizeUseCase


def make_config(retries: int = 1) -> TTSConfig:
    return TTSConfig("vi-VN-NamMinhNeural", "+0%", "+0Hz", "+0%", retries, 1.0, None)


def make_service(retries: int = 1) -> SynthesizeUseCase:
    return SynthesizeUseCase(AsyncMock(), make_config(retries))

def test_synthesize_with_retry_recovers_after_failure(tmp_path: Path, monkeypatch):
    service = make_service(retries=1)
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"partial")
    cues = [SubtitleCue(0, 100_000, "Xin")]
    service.engine.synthesize = AsyncMock(side_effect=[RuntimeError("network"), SynthesisResult(audio_path, cues)])
    monkeypatch.setattr("tts_cli.application.synthesize.asyncio.sleep", AsyncMock())

    result = asyncio.run(service.synthesize_with_retry("Xin", audio_path))

    assert result.word_cues == cues
    assert service.engine.synthesize.await_count == 2
    assert not audio_path.exists()


def test_synthesize_with_retry_raises_after_all_attempts(tmp_path: Path, monkeypatch):
    service = make_service(retries=1)
    audio_path = tmp_path / "audio.mp3"
    service.engine.synthesize = AsyncMock(side_effect=RuntimeError("network"))
    monkeypatch.setattr("tts_cli.application.synthesize.asyncio.sleep", AsyncMock())

    with pytest.raises(RuntimeError, match="2 lần thử"):
        asyncio.run(service.synthesize_with_retry("Xin", audio_path))

    assert service.engine.synthesize.await_count == 2


def test_generate_dry_run_does_not_create_project_artifacts(tmp_path: Path, capsys):
    number = asyncio.run(
        make_service(retries=0).execute(
            "Xin chào.", tmp_path, "phrase", 8, formats="mp3,srt,json", dry_run=True
        )
    )

    assert number == 1
    assert not (tmp_path / "001").exists()
    assert "audio.mp3" in capsys.readouterr().out

def test_generate_rejects_existing_project_without_overwrite(tmp_path: Path):
    (tmp_path / "001").mkdir()

    with pytest.raises(FileExistsError):
        asyncio.run(
            make_service(retries=0).execute(
                "Xin", tmp_path, "phrase", 8, project_number=1
            )
        )


def test_generate_cleans_new_folder_when_synthesis_fails(tmp_path: Path):
    service = make_service(retries=0)

    async def fail_synthesize(text: str, audio_path: Path) -> SynthesisResult:
        audio_path.write_bytes(b"partial")
        raise RuntimeError("synthesis failed")

    service.engine.synthesize = fail_synthesize

    with pytest.raises(RuntimeError, match="synthesis failed"):
        asyncio.run(service.execute("Xin", tmp_path, "phrase", 8))

    assert not (tmp_path / "001").exists()


def test_generate_dispatches_selected_output_formats(tmp_path: Path):
    service = make_service(retries=0)
    cues = [
        SubtitleCue(0, 100_000, "Xin"),
        SubtitleCue(100_000, 200_000, "chào."),
    ]

    async def fake_synthesize(text: str, audio_path: Path) -> SynthesisResult:
        audio_path.write_bytes(b"audio")
        return SynthesisResult(audio_path, cues)

    service.synthesize_with_retry = fake_synthesize
    number = asyncio.run(
        service.execute("Xin chào.", tmp_path, "sentence", 8, formats="srt,vtt,json")
    )

    folder = tmp_path / "001"
    assert number == 1
    assert not (folder / "audio.mp3").exists()
    assert (folder / "subtitle.srt").exists()
    assert (folder / "subtitle.vtt").exists()
    assert (folder / "subtitle.json").exists()


def test_batch_continues_after_error_when_requested(tmp_path: Path):
    source = tmp_path / "scripts"
    source.mkdir()
    (source / "one.txt").write_text("Een", encoding="utf-8")
    (source / "two.txt").write_text("Twee", encoding="utf-8")
    output = tmp_path / "output"
    service = SimpleNamespace(execute=AsyncMock(side_effect=[RuntimeError("failed"), None]))
    batch = BatchProcessUseCase(cast(SynthesizeUseCase, service))

    asyncio.run(
        batch.execute(source, output, False, "phrase", 8, 1, False, True, False, "mp3,srt")
    )

    assert service.execute.await_count == 2


def test_progress_bar_clamps_values_and_finishes(capsys):
    progress = ProgressBar(2, "Test")

    progress.update(5, "done")
    progress.finish()

    assert "Test: 2/2 done" in capsys.readouterr().err


def test_find_input_files_returns_supported_files_in_sorted_order(tmp_path: Path):
    (tmp_path / "b.vtt").write_text("WEBVTT", encoding="utf-8")
    (tmp_path / "A.txt").write_text("A", encoding="utf-8")
    (tmp_path / "ignored.md").write_text("ignored", encoding="utf-8")

    assert [path.name for path in find_input_files(tmp_path, recursive=False)] == ["A.txt", "b.vtt"]


def test_batch_skips_complete_project_for_selected_formats(tmp_path: Path):
    source = tmp_path / "scripts"
    source.mkdir()
    (source / "one.txt").write_text("Een", encoding="utf-8")
    output = tmp_path / "output"
    folder = output / "001"
    folder.mkdir(parents=True)
    (folder / "audio.mp3").write_bytes(b"audio")
    (folder / "subtitle.json").write_text("[]", encoding="utf-8")

    service = SimpleNamespace(execute=AsyncMock())
    batch = BatchProcessUseCase(cast(SynthesizeUseCase, service))
    asyncio.run(
        batch.execute(
            source, output, False, "phrase", 8, 1, True, False, False, "mp3,json"
        )
    )

    service.execute.assert_not_awaited()