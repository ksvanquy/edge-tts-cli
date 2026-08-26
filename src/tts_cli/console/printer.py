import sys


def print_error(message: str) -> None:
    print(f"❌ {message}", file=sys.stderr)


def print_warning(message: str) -> None:
    print(f"⚠️ {message}")


def print_info(message: str) -> None:
    print(f"ℹ️ {message}")
