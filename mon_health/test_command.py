from datetime import datetime

import pytest

from .command import (
    CommandNotFound,
    HelpCommand,
    InvalidDate,
    parse_date,
    setup_commands,
)


class TestCommand:
    description = "Test."


COMMAND_TABLE = {
    "test1": TestCommand,
    "test2": TestCommand,
}

setup_commands(None, COMMAND_TABLE)


class TestHelpCommand:
    @pytest.mark.parametrize(
        "args,expected",
        [
            ("", ["test1               Test.", "test2               Test."]),
            ("test1", ["test1               Test."]),
        ],
    )
    def test_given_valid_args(self, args, expected):
        assert HelpCommand.execute(args) == expected

    def test_given_invalid_args(self):
        with pytest.raises(CommandNotFound):
            HelpCommand.execute("nonexistent command")


@pytest.mark.parametrize(
    "string,expected",
    [
        ("1", datetime(day=1, month=datetime.now().month, year=datetime.now().year)),
        (
            "01",
            datetime(day=1, month=datetime.now().month, year=datetime.now().year),
        ),
        ("12/1", datetime(day=12, month=1, year=datetime.now().year)),
        ("1/01", datetime(day=1, month=1, year=datetime.now().year)),
        ("1/12", datetime(day=1, month=12, year=datetime.now().year)),
        ("1/12/1920", datetime(day=1, month=12, year=1920)),
    ],
)
def test_parse_date_given_valid_input(string, expected):
    assert parse_date(string) == expected


@pytest.mark.parametrize("string", ["", "a", "1//", "1/0t", "6/6/2020/20"])
def test_parse_date_given_invalid_input(string):
    with pytest.raises(InvalidDate):
        parse_date(string)
