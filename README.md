# Edge TTS CLI

### UI desktop Windows
UI desktop PySide6 được cung cấp dưới dạng dependency tùy chọn và dùng lại các

python -m pip install -e ".[desktop]"
tts-desktop
```powershell
python -m tts_cli generate -f scripts\script1.txt
python -m tts_cli generate -f scripts\script3.srt
python -m tts_cli generate -f scripts\script4.vtt
python -m tts_cli generate -f scripts\script3.srt --formats mp3,srt,vtt,json
python -m tts_cli generate -f scripts\script1.txt --voice vi-VN-NamMinhNeural --rate +0% --pitch +0Hz --volume +0%

Ứng dụng mở trực tiếp trong cửa sổ Windows, không cần browser hoặc web server.
UI có các mode Generate, Batch, Transcribe và Voices; provider Google/Whisper
vẫn cần cài extra tương ứng. UI không gọi trực tiếp SDK, FFmpeg hoặc filesystem
output ngoài các use case/adapter đã được wire ở composition root.
python -m tts_cli batch scripts --recursive
```

Shortcut này chỉ áp dụng cho `generate`. Các lệnh `batch` và `voices` vẫn cần ghi rõ tên subcommand.
`tts-ui` vẫn là alias tương thích tới cùng PySide6 application:
The `generate` command accepts UTF-8 `TXT`, `SRT`, and `VTT` files. For subtitle files, cue numbers, timestamps, and WebVTT metadata are removed before the text is sent to Edge TTS. By default, each project contains `audio.mp3` and `subtitle.srt`. Use `--formats` with a comma-separated list of `mp3`, `srt`, `vtt`, and `json` to choose the output artifacts. The subtitle formats are written as `subtitle.srt`, `subtitle.vtt`, and `subtitle.json`.

Output handling is separated into an output adapter. `OutputResolver` dispatches each selected format to its own handler and manages the artifact paths in the numbered project folder. If synthesis or output writing fails, incomplete artifacts from the current run are cleaned up automatically.

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

The project uses a layered `src` layout with one-way dependencies:

```text
CLI
	-> application use cases
			-> services
			-> core contracts and models
	-> providers and adapters (composition root)

services
	-> core

providers
	-> core

adapters
	-> core
```

The canonical package structure is:

```text
src/tts_cli/
├── core/         Domain models, provider interfaces, config, errors, capabilities
├── application/  Synthesize, batch, transcribe, and voice-listing use cases
├── services/     Retry, project lifecycle, batch discovery, transcription, voice catalog
├── providers/    Edge/Google TTS, Whisper STT, and FFmpeg integrations
├── adapters/     Input, output, subtitle, and console I/O implementations
└── cli/          Argument parser and composition root
```

`core` contains framework-independent contracts and domain models. `application`
coordinates user workflows. `services` contains reusable policies and orchestration
such as retries, project numbering, batch file discovery, media transcription, and
voice filtering. `providers` owns external SDK and system integrations, while
`adapters` owns filesystem, subtitle, output-format, and console I/O. The CLI wires
these components together without making the application layer depend on a specific
provider implementation.

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
| `-v`, `--voice` | Voice name for the selected TTS engine | `vi-VN-NamMinhNeural` |
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

### UI web

UI desktop PySide6 được cung cấp dưới dạng dependency tùy chọn và dùng lại các
application use case hiện có:

```powershell
python -m pip install -e ".[desktop]"
tts-desktop
```

Ứng dụng mở trực tiếp trong cửa sổ Windows, không cần browser hoặc web server.
UI có các mode Generate, Batch, Transcribe và Voices; provider Google/Whisper
vẫn cần cài extra tương ứng. UI không gọi trực tiếp SDK, FFmpeg hoặc filesystem
output ngoài các use case/adapter đã được wire ở composition root.

### UI desktop Windows

`tts-ui` là alias tương thích tới cùng PySide6 application. Trong môi trường
phát triển, có thể chạy trực tiếp:

```powershell
python -m tts_cli.ui.desktop
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

Workflow Whisper cần hai thành phần riêng:

1. Package Python `faster-whisper` trong môi trường ảo.
2. Hai executable hệ thống `ffmpeg.exe` và `ffprobe.exe` trong `PATH`.

#### Cài FFmpeg trên Windows

Cách nhanh nhất là dùng `winget`:

```powershell
winget install Gyan.FFmpeg.Shared
```

Đóng và mở lại PowerShell sau khi cài. Nếu máy không có `winget`, tải bản Windows
Essentials từ [FFmpeg Builds by gyan.dev](https://www.gyan.dev/ffmpeg/builds/),
giải nén, ví dụ vào `C:\ffmpeg`, rồi thêm thư mục `C:\ffmpeg\bin` vào **User
Path** hoặc **System Path** trong `System Properties > Environment Variables`.

Có thể thêm tạm vào PATH của phiên PowerShell hiện tại để kiểm tra:

```powershell
$env:Path += ";C:\ffmpeg\bin"
```

Kiểm tra cả hai executable:

```powershell
Get-Command ffmpeg
Get-Command ffprobe
ffmpeg -version
ffprobe -version
```

Nếu `Get-Command` không tìm thấy lệnh, hãy mở một terminal mới sau khi cập nhật
PATH. Dự án gọi trực tiếp cả `ffmpeg` và `ffprobe`, nên chỉ cài một trong hai
không đủ.

#### Cài Whisper cho project

Cài Whisper local và đảm bảo `ffmpeg`/`ffprobe` đã được kiểm tra ở bước trên:

```powershell
python -m pip install -e ".[whisper]"
```

Transcribe file audio trực tiếp hoặc video thông qua audio track:

```powershell
python -m tts_cli transcribe audio.wav --engine whisper --output subtitle.srt
python -m tts_cli transcribe audio.mp3 --engine whisper --output subtitle.srt
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

python -m pip install -e ".[desktop]"
tts-desktop
python -m tts_cli.ui.desktop

venv\Scripts\python.exe -m tts_cli.ui.desktop
tts-desktop
venv\Scripts\python.exe -m build
venv\Scripts\python.exe -m pip install --force-reinstall dist\*.whl