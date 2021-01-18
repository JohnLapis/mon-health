import pytest

from mon_health import parse_command, run_command, setup

setup()


@pytest.mark.parametrize(
    "command,expected",
    [
        ("a", ("a", "")),
        ("a b", ("a", "b")),
        ("a b c", ("a", "b c")),
    ],
)
def test_parse_command_given_valid_input(command, expected):
    assert parse_command(command) == expected


def test_parse_command_given_invalid_input(capsys):
    run_command("$@'_'")
    captured = capsys.readouterr()
    assert captured.out == "A command should be composed of lower-case letters.\n"


def test_run_command(capsys):
    run_command("help help")
    captured = capsys.readouterr()
    assert captured.out == "help                Prints this help.\n"


def test_run_command_given_invalid_input(capsys):
    name = "nonexistent_command"
    run_command(name)
    captured = capsys.readouterr()
    assert captured.out == f"Command '{name}' does not exist.\n"
