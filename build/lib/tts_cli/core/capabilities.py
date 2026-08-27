from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCapabilities:
    word_timing: bool = False
    sentence_timing: bool = False
    streaming: bool = False
    voice_listing: bool = False
