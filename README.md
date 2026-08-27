# Edge TTS CLI

Convert text files or direct text to numbered folders containing configurable output artifacts.

## Usage

```powershell
python -m tts_cli generate -f scripts\script1.txt
python -m tts_cli generate -f scripts\script3.srt
python -m tts_cli generate -f scripts\script4.vtt
python -m tts_cli generate -f scripts\script3.srt --formats mp3,srt,vtt,json
python -m tts_cli generate -f scripts\script1.txt --voice vi-VN-NamMinhNeural --rate +0% --pitch +0Hz --volume +0%

python -m tts_cli batch scripts
python -m tts_cli batch scripts --recursive
python -m tts_cli batch scripts --formats mp3,srt,json
python -m tts_cli batch scripts --voice vi-VN-NamMinhNeural --rate +0% --pitch +0Hz --volume +0%
python -m tts_cli voices --language vi
python -m tts_cli transcribe scripts\audio.wav --engine whisper --output subtitle.srt
python -m tts_cli transcribe videos\input.mp4 --engine whisper --language vi --output subtitle.srt
```

`generate` là subcommand tường minh. Khi chỉ tạo một project từ text hoặc file, có thể bỏ qua `generate`; CLI sẽ tự nhận diện lệnh này:

```powershell
python -m tts_cli -f scripts\script1.txt --voice vi-VN-NamMinhNeural --rate +0% --pitch +0Hz --volume +0%
python -m tts_cli -t "Xin chào" --voice vi-VN-NamMinhNeural
```

Shortcut này chỉ áp dụng cho `generate`. Các lệnh `batch` và `voices` vẫn cần ghi rõ tên subcommand.

The `generate` command accepts UTF-8 `TXT`, `SRT`, and `VTT` files. For subtitle files, cue numbers, timestamps, and WebVTT metadata are removed before the text is sent to Edge TTS. By default, each project contains `audio.mp3` and `subtitle.srt`. Use `--formats` with a comma-separated list of `mp3`, `srt`, `vtt`, and `json` to choose the output artifacts. The subtitle formats are written as `subtitle.srt`, `subtitle.vtt`, and `subtitle.json`.

Output handling is separated into an Output Module. `OutputResolver` dispatches each selected format to its own handler and manages the artifact paths in the numbered project folder. If synthesis or output writing fails, incomplete artifacts from the current run are cleaned up automatically.

Batch mode scans `.txt`, `.srt`, and `.vtt` files, then maps them in sorted order to folders beginning at `--start`. Existing folders are overwritten by default, so rerunning the same batch updates `001`, `002`, and so on instead of creating new projects. Use `--skip-existing` to leave complete projects unchanged according to the selected `--formats`.

Generate and batch processing display progress in an interactive terminal. Generate reports the TTS, subtitle, and output stages; batch reports the current file and overall progress. When output is redirected or captured, progress is printed as one line per step on stderr so the result summary remains readable. On failure, the CLI prints a friendly error and a suggested next step. Press `Ctrl+C` to cancel; the command exits with status `130`.

## Voices

The default voice is `vi-VN-HoaiMyNeural`. List available voices and filter the results with `--language`, `--gender`, or `--search`:

```powershell
python -m tts_cli voices
python -m tts_cli voices --language vi
python -m tts_cli voices --language en --gender Female
python -m tts_cli voices --search Neural
```

Use a voice's `ShortName` with `-v` or `--voice` when generating audio:

```powershell
python -m tts_cli generate -f scripts\script1.txt --voice vi-VN-NamMinhNeural
```

`--language` matches the locale or voice name, `--gender` accepts `Male` or `Female`, and `--search` searches the voice name, locale, and friendly name.

## Architecture

The project uses a layered `src` layout:

```text
CLI
	-> application use cases
		-> input readers and resolver
		-> providers/tts (Edge, Google)
		-> providers/stt (Whisper, Google, ...)
		-> providers/media (FFmpeg)
		-> subtitle and output handlers
```

`core` defines the provider boundaries and domain models. `application` contains
the `SynthesizeUseCase`, `BatchProcessUseCase`, and `TranscribeUseCase` workflows.
`providers` contains integrations for TTS, speech-to-text, and media processing.
`input` owns text normalization and TXT/SRT/VTT readers. `subtitle` and `output`
remain provider-independent and are responsible for cue processing and artifact
writing.

## TTS Parameters

Pass TTS parameters after the `generate` or `batch` command. They are not global options for `python -m tts_cli` by itself.

```powershell
python -m tts_cli generate `
	-f scripts\script1.txt `
	--voice vi-VN-NamMinhNeural `
	--rate +0% `
	--pitch +0Hz `
	--volume +0%
```

The same parameters can be used when processing a folder in batch mode:

```powershell
python -m tts_cli batch scripts `
	--voice vi-VN-NamMinhNeural `
	--rate +0% `
	--pitch +0Hz `
	--volume +0%
```

Available parameters:

| Option | Description | Example |
| --- | --- | --- |
| `-v`, `--voice` | Edge TTS voice `ShortName` | `vi-VN-NamMinhNeural` |
| `--rate` | Reading speed adjustment | `+10%`, `-10%` |
| `--pitch` | Voice pitch adjustment | `+2Hz`, `-2Hz` |
| `--volume` | Output volume adjustment | `+0%`, `-10%` |
| `--retries` | Number of retries after a failed request | `3` |
| `--timeout` | Request timeout in seconds | `60` |
| `--proxy` | Proxy used by Edge TTS | `http://127.0.0.1:8080` |

## Development

Create and activate a virtual environment in PowerShell, then install the project:

```powershell
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

### Google Cloud Text-to-Speech

Google TTS là dependency tùy chọn. Cài project cùng Google Cloud client:

```powershell
python -m pip install -e ".[google]"
```

Tạo một Google Cloud project, bật **Cloud Text-to-Speech API**, tạo service account
và tải file JSON credentials. Trỏ biến môi trường
`GOOGLE_APPLICATION_CREDENTIALS` tới file đó:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\service-account.json"
```

Kiểm tra danh sách voice Google:

```powershell
python -m tts_cli voices --engine google --language en-US
```

Sử dụng tên voice Google khi tạo audio:

```powershell
python -m tts_cli generate `
	--engine google `
	--voice en-US-Neural2-A `
	--text "Hello from Google Cloud Text-to-Speech"
```

Google Cloud TTS tạo audio MP3 nhưng provider hiện không trả về word timing,
vì vậy subtitle timing có thể rỗng. Edge TTS vẫn là engine mặc định và hỗ trợ
`WordBoundary` để tạo subtitle theo từ.

### Audio/video to SRT

Cài Whisper local và đảm bảo `ffmpeg` có trong `PATH`:

```powershell
python -m pip install -e ".[whisper]"
```

Transcribe file audio trực tiếp hoặc video thông qua audio track:

```powershell
python -m tts_cli transcribe audio.wav --engine whisper --output subtitle.srt
python -m tts_cli transcribe video.mp4 --engine whisper --language vi --model-size small
```

Whisper mặc định chạy bằng CPU với model `base`. Dùng `--device cuda` nếu môi
trường đã cài CUDA tương thích với `faster-whisper`.

After activation, run the CLI with the virtual environment's Python:

```powershell
python -m tts_cli generate -f scripts\script1.txt
```

Run the test suite with:

```powershell
python -m pytest
```

Run focused tests while developing:

```powershell
python -m pytest tests\test_text.py tests\test_subtitle.py -q
python -m pytest tests\test_services.py tests\test_edge_tts_engine.py -q
python -m pytest tests\test_output.py tests\test_cli.py tests\test_commands.py tests\test_voices.py -q
```

The tests mock Edge TTS network calls, so the test suite runs offline. The current suite covers input normalization, TXT/SRT/VTT parsing, subtitle cue generation, validation, output handlers, CLI parsing, retry behavior, batch processing, progress, and voice filtering.