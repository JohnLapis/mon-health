import pytest

from mon_health import CommandNotFound, parse_command, run_command, setup

setup()


@pytest.mark.parametrize(
    "command,expected",
    [
        ("a", ("a", "")),
        ("a b", ("a", "b")),
        ("a b c", ("a", "b c")),
    ],
)
def test_parse_command(command, expected):
    assert parse_command(command) == expected


def test_run_command(capsys):
    run_command("help help")
    captured = capsys.readouterr()
    assert captured.out == "help                Prints this help.\n"


def test_run_command_given_invalid_input(command, expected):
    with pytest.raises(CommandNotFound):
        run_command(command)
