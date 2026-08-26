from tts_cli.output.project import create_output_folder, get_next_number


def test_next_number_and_folder_format(tmp_path):
    create_output_folder(tmp_path, 1)
    (tmp_path / "005").mkdir()
    assert get_next_number(tmp_path) == 6
