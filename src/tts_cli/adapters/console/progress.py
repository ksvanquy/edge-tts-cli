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
        print(f"[{percent:3d}%] {self.label}: {detail}".rstrip(), file=sys.stderr, flush=not self.enabled)

    def finish(self) -> None:
        return None
