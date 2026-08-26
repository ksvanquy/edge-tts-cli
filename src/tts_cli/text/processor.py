from pathlib import Path


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.strip() for line in text.split("\n") if line.strip()).strip()


def read_txt_file(path: Path) -> str:
    from tts_cli.text.resolver import InputResolver

    return InputResolver().resolve_file(path).text


def read_input_file(path: Path) -> str:
    from tts_cli.text.resolver import InputResolver

    return InputResolver().resolve_file(path).text


def get_text_from_args(args) -> str:
    from tts_cli.text.resolver import InputResolver

    return InputResolver().resolve(args).text
