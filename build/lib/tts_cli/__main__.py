import asyncio
import sys

from tts_cli.cli.commands import async_main, normalize_argv
from tts_cli.cli.parser import build_parser
from tts_cli.adapters.console.printer import print_error


def error_hint(exc: Exception) -> str | None:
    if isinstance(exc, FileNotFoundError):
        return "kiểm tra lại đường dẫn file hoặc thư mục input."
    if isinstance(exc, IsADirectoryError):
        return "hãy truyền đường dẫn tới một file input cụ thể."
    if isinstance(exc, FileExistsError):
        return "dùng --overwrite để ghi đè hoặc đổi --output/--start."
    if isinstance(exc, UnicodeDecodeError):
        return "hãy lưu file input ở encoding UTF-8."
    if isinstance(exc, TimeoutError):
        return "tăng --timeout hoặc kiểm tra kết nối mạng."
    if isinstance(exc, ConnectionError):
        return "kiểm tra kết nối mạng, voice và --proxy nếu đang dùng proxy."
    if isinstance(exc, ValueError):
        return "chạy `python -m tts_cli <command> --help` để xem cú pháp hợp lệ."
    return None


def main() -> None:
    parser = build_parser()
    args = parser.parse_args(normalize_argv(sys.argv[1:]))
    try:
        sys.exit(asyncio.run(async_main(args)))
    except KeyboardInterrupt:
        print("\n⚠️ Đã hủy.")
        sys.exit(130)
    except Exception as exc:
        print_error(str(exc), error_hint(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
