from datetime import datetime

import pytest

from .command import (
    CommandNotFound,
    HelpCommand,
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




