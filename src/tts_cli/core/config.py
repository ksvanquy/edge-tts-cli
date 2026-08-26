import re


def normalize_rate(value: str) -> str:
    match = re.fullmatch(r"([+-]?\d+)(%)?", value.strip())
    if not match:
        raise ValueError(f"Rate không hợp lệ: {value}\nVí dụ: 10%, -10%, 0%")
    sign = "" if match.group(1).startswith(("+", "-")) else "+"
    return f"{sign}{match.group(1)}%"


def normalize_pitch(value: str) -> str:
    match = re.fullmatch(r"([+-]?\d+)(Hz)?", value.strip(), re.IGNORECASE)
    if not match:
        raise ValueError(f"Pitch không hợp lệ: {value}\nVí dụ: 5Hz, -5Hz, 0Hz")
    sign = "" if match.group(1).startswith(("+", "-")) else "+"
    return f"{sign}{match.group(1)}Hz"


def validate_rate(value: str) -> None:
    normalize_rate(value)


def validate_pitch(value: str) -> None:
    normalize_pitch(value)


def validate_volume(value: str) -> None:
    normalize_rate(value)


def validate_args(args) -> None:
    args.rate = normalize_rate(args.rate)
    args.pitch = normalize_pitch(args.pitch)
    args.volume = normalize_rate(args.volume)
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
