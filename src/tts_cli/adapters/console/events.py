"""Console renderer for application notices."""

import sys

from tts_cli.core.events import ApplicationNotice


class ConsoleNoticeRenderer:
    def __call__(self, event: ApplicationNotice) -> None:
        prefix = {
            "debug": "DEBUG",
            "info": "INFO",
            "warning": "WARN",
            "error": "ERROR",
        }.get(event.level, event.level.upper())
        print(f"[{prefix}] {event.message}", file=sys.stderr)