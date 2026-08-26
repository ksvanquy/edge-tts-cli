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
```

The `generate` command accepts UTF-8 `TXT`, `SRT`, and `VTT` files. For subtitle files, cue numbers, timestamps, and WebVTT metadata are removed before the text is sent to Edge TTS. By default, each project contains `audio.mp3` and `subtitle.srt`. Use `--formats` with a comma-separated list of `mp3`, `srt`, `vtt`, and `json` to choose the output artifacts. The subtitle formats are written as `subtitle.srt`, `subtitle.vtt`, and `subtitle.json`.

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

After activation, run the CLI with the virtual environment's Python:

```powershell
python -m tts_cli generate -f scripts\script1.txt
```

Run the test suite with:

```powershell
python -m pytest
``