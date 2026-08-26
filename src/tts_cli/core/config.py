import re


def validate_rate(value: str) -> None:
    if not re.fullmatch(r"[+-]\d+%", value):
        raise ValueError(f"Rate không hợp lệ: {value}\nVí dụ: +10%, -10%, +0%")


def validate_pitch(value: str) -> None:
    if not re.fullmatch(r"[+-]\d+Hz", value, re.IGNORECASE):
        raise ValueError(f"Pitch không hợp lệ: {value}\nVí dụ: +5Hz, -5Hz, +0Hz")


def validate_volume(value: str) -> None:
    if not re.fullmatch(r"[+-]\d+%", value):
        raise ValueError(f"Volume không hợp lệ: {value}\nVí dụ: +10%, -10%, +0%")


def validate_args(args) -> None:
    validate_rate(args.rate)
    validate_pitch(args.pitch)
    validate_volume(args.volume)
    if args.retries < 0:
        raise ValueError("--retries phải >= 0")
    if args.timeout <= 0:
        raise ValueError("--timeout phải > 0")
    if args.max_words <= 0:
        raise ValueError("--max-words phải > 0")
    if args.start < 1:
        raise ValueError("--start phải >= 1")
    if args.overwrite and args.skip_existing:
        raise ValueError("Không thể dùng đồng thời --overwrite và --skip-existing.")
