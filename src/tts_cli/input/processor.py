def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.strip() for line in text.split("\n") if line.strip()).strip()
