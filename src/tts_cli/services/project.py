import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    number: int
    folder: Path
    audio: Path


class ProjectService:
    def next_number(self, output_root: Path, start: int = 1) -> int:
        if not output_root.exists():
            return start
        numbers = [
            int(match.group(1))
            for item in output_root.iterdir()
            if item.is_dir() and (match := re.fullmatch(r"(\d+)", item.name))
        ]
        return max(numbers, default=start - 1) + 1

    def paths(self, output_root: Path, start: int = 1, number: int | None = None) -> ProjectPaths:
        project_number = number if number is not None else self.next_number(output_root, start)
        folder = output_root / f"{project_number:03d}"
        return ProjectPaths(project_number, folder, folder / "audio.mp3")


def get_next_number(output_root: Path, start: int = 1) -> int:
    return ProjectService().next_number(output_root, start)


def create_output_folder(output_root: Path, number: int) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    folder = output_root / f"{number:03d}"
    folder.mkdir(parents=True, exist_ok=False)
    return folder


__all__ = ["ProjectPaths", "ProjectService", "create_output_folder", "get_next_number"]
