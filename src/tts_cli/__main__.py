import asyncio
import sys

from tts_cli.cli.commands import async_main, normalize_argv
from tts_cli.cli.parser import build_parser
from tts_cli.console.printer import print_error


def main() -> None:
    parser = build_parser()
    args = parser.parse_args(normalize_argv(sys.argv[1:]))
    try:
        sys.exit(asyncio.run(async_main(args)))
    except KeyboardInterrupt:
        print("\n⚠️ Đã hủy.")
        sys.exit(130)
    except Exception as exc:
        print_error(str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
