from pathlib import Path

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".flv", ".wmv", ".m4v"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac", ".wma"}


def is_video_file(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def is_audio_file(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_EXTENSIONS
