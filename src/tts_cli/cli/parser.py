import argparse

from tts_cli.core.constants import (
    DEFAULT_MAX_WORDS, DEFAULT_OUTPUT, DEFAULT_PITCH, DEFAULT_RATE,
    DEFAULT_RETRIES, DEFAULT_SUBTITLE_MODE, DEFAULT_TIMEOUT, DEFAULT_VOICE,
    DEFAULT_VOLUME, VERSION,
)


def add_tts_options(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("TTS")
    group.add_argument("-v", "--voice", default=DEFAULT_VOICE)
    group.add_argument("--rate", default=DEFAULT_RATE)
    group.add_argument("--pitch", default=DEFAULT_PITCH)
    group.add_argument("--volume", default=DEFAULT_VOLUME)
    group.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    group.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    group.add_argument("--proxy", default=None)


def add_subtitle_options(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("Subtitle")
    group.add_argument("--subtitle-mode", choices=["phrase", "sentence", "word"], default=DEFAULT_SUBTITLE_MODE)
    group.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS)


def add_output_options(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("Output")
    group.add_argument("-o", "--output", default=DEFAULT_OUTPUT)
    group.add_argument("--start", type=int, default=1)
    group.add_argument("--overwrite", action="store_true")
    group.add_argument("--skip-existing", action="store_true")
    group.add_argument("--dry-run", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tts", description="Edge TTS CLI - TXT/Text -> MP3 + SRT")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    subparsers = parser.add_subparsers(dest="command")
    generate = subparsers.add_parser("generate", help="Tạo một project TTS")
    input_group = generate.add_argument_group("Input")
    input_group.add_argument("-t", "--text")
    input_group.add_argument("-f", "--file")
    add_tts_options(generate)
    add_subtitle_options(generate)
    add_output_options(generate)
    batch = subparsers.add_parser("batch", help="Xử lý nhiều file TXT")
    batch.add_argument("directory")
    batch.add_argument("--recursive", action="store_true")
    batch.add_argument("--continue-on-error", action="store_true")
    add_tts_options(batch)
    add_subtitle_options(batch)
    add_output_options(batch)
    voices = subparsers.add_parser("voices", help="Liệt kê voice")
    voices.add_argument("--language")
    voices.add_argument("--gender", choices=["Male", "Female"])
    voices.add_argument("--search")
    return parser
