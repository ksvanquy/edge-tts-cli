import sys


def print_error(message: str, hint: str | None = None) -> None:
    print(f"❌ {message}", file=sys.stderr)
    if hint:
        print(f"   Gợi ý: {hint}", file=sys.stderr)


def print_warning(message: str) -> None:
    print(f"⚠️ {message}")


def print_info(message: str) -> None:
    print(f"ℹ️ {message}")
