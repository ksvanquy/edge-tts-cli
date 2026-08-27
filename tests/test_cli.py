from tts_cli.cli.parser import build_parser


def test_generate_parser_reads_tts_and_output_options():
    args = build_parser().parse_args(
        [
            "generate",
            "-f",
            "script.txt",
            "--voice",
            "vi-VN-NamMinhNeural",
            "--rate",
            "+10%",
            "--pitch",
            "+2Hz",
            "--volume",
            "+0%",
            "--formats",
            "mp3,srt,json",
        ]
    )

    assert args.file == "script.txt"
    assert args.voice == "vi-VN-NamMinhNeural"
    assert args.rate == "+10%"
    assert args.pitch == "+2Hz"
    assert args.volume == "+0%"
    assert args.formats == "mp3,srt,json"


def test_batch_parser_reads_batch_options():
    args = build_parser().parse_args(["batch", "scripts", "--recursive", "--skip-existing"])

    assert args.command == "batch"
    assert args.directory == "scripts"
    assert args.recursive is True
    assert args.skip_existing is True


def test_parser_accepts_google_engine_for_generate_and_voices():
    generate_args = build_parser().parse_args(["generate", "--engine", "google", "--text", "Xin"])
    voices_args = build_parser().parse_args(["voices", "--engine", "google"])

    assert generate_args.engine == "google"
    assert voices_args.engine == "google"