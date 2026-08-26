import asyncio

import pytest

from tts_cli.cli.commands import async_main
from tts_cli.cli.parser import build_parser


def test_generate_rejects_text_and_file_together():
    args = build_parser().parse_args(["generate", "--text", "Xin", "--file", "script.txt"])

    with pytest.raises(ValueError, match="--text và --file"):
        asyncio.run(async_main(args))