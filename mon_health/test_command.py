from datetime import datetime

import pytest

from .command import (
    CommandNotFound,
    HelpCommand,
    InsertCommand,
    setup_commands,
)


class TestHelpCommand:
    @classmethod
    def setup_class(cls):
        class FakeDb:
            Food = None


        class TestCommand:
            description = "Test."

        COMMAND_TABLE = {
            "test1": TestCommand,
            "test2": TestCommand,
        }

        setup_commands(FakeDb(), COMMAND_TABLE)

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


class TestInsertCommand:
    @classmethod
    def setup_class(cls):
        from . import db

        setup_commands(db)
        cls.Food = db.Food

    @pytest.mark.parametrize(
        "args,expected",
        [
            ("a", ["a"]),
            ("a, b  ", ["a", "b"]),
            (" a  , b  ", ["a", "b"]),
        ],
    )
    def test_parse_args_given_valid_args(self, args, expected):
        assert InsertCommand.parse_args(args) == expected

    @pytest.mark.parametrize(
        "args",
        ["batata"],
    )
    def test_execute_given_valid_args(self, args):
        InsertCommand.execute(args)
        inserted_id = (
            (
                self.Food.select()
                .where(self.Food.date == datetime.now().date())
                .order_by(self.Food.time.desc())
                .limit(1)
            )
            .get()
            .id
        )
        assert self.Food.get_by_id(inserted_id).name == args
        assert self.Food.delete_by_id(inserted_id) == 1
