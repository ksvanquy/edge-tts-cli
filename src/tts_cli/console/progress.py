import sys


class ProgressBar:
    def __init__(self, total: int, label: str = "Tiến độ"):
        self.total = max(total, 1)
        self.label = label
        self.current = 0
        self.enabled = sys.stderr.isatty()

    def update(self, current: int, detail: str = "") -> None:
        self.current = min(max(current, 0), self.total)
        percent = self.current * 100 // self.total
        if self.enabled:
            width = 24
            filled = width * self.current // self.total
            bar = "=" * filled + ">" + " " * max(width - filled - 1, 0)
            print(f"\r{self.label} [{bar}] {percent:3d}% {detail}"[:120], end="", file=sys.stderr, flush=True)
        else:
            print(f"{self.label}: {self.current}/{self.total} {detail}".rstrip(), file=sys.stderr)

    def finish(self) -> None:
        if self.enabled:
            print(file=sys.stderr)