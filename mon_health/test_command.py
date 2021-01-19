import random
import re
from datetime import datetime, time

import pytest

from .command import (
    CommandNotFound,
    FindCommand,
    HelpCommand,
    InsertCommand,
    InvalidArgs,
    UpdateCommand,
    setup_commands,
)


def get_random_string(length):
    letters = "abcdefghijklmnopqrstuvwxyz"
    return "".join(random.choice(letters) for i in range(length))


def now():
    return datetime.now()


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

    def test_execute_given_valid_args(self):
        random_string = get_random_string(20)
        InsertCommand.execute(random_string)
        inserted_id = (
            self.Food.select().where(self.Food.name == random_string).get().id
        )
        assert self.Food.delete_by_id(inserted_id) == 1


class TestFindCommand:
    @classmethod
    def setup_class(cls):
        from . import db

        setup_commands(db)
        cls.Food = db.Food

    @pytest.mark.parametrize(
        "args,expected",
        [
            (
                "hotdog;",
                lambda q, Food: q.where(Food.name == "hotdog").order_by(Food.date),
            ),
            (
                "toDAY",
                lambda q, Food: (
                    q.where(Food.date == datetime.now().date()).order_by(Food.date)
                ),
            ),
            ("sort date", lambda q, Food: q.order_by(Food.date)),
            ("order BY -date", lambda q, Food: q.order_by(Food.date.desc())),
            ("LIMIT 5", lambda q, Food: q.limit("5")),
            (
                "1/01 5h    sort  date LImit 1",
                lambda q, Food: (
                    q.where(
                        (Food.date == datetime(day=1, month=1, year=now().year))
                        & Food.time.between(
                            time(hour=5, minute=00), time(hour=5, minute=59)
                        )
                    )
                    .order_by(Food.date)
                    .limit("1")
                ),
            ),
        ],
    )
    def test_parse_args_given_valid_args(self, args, expected):
        received_query = FindCommand.parse_args(args)
        expected_query = expected(self.Food.select(), self.Food)

        for row1, row2 in zip(received_query, expected_query):
            assert row1 == row2

    def test_execute_given_valid_args(self):
        random_string = get_random_string(20)
        self.Food.insert(name=random_string).execute()

        output = FindCommand.execute(random_string + ";")

        assert len(output) == 2
        id = re.match(r"\d+", output[1]).group()
        food = self.Food.get_by_id(id)
        assert self.Food.delete_by_id(id) == 1
        assert food.name == random_string


class TestUpdateCommand:
    @classmethod
    def setup_class(cls):
        from . import db

        setup_commands(db)
        cls.Food = db.Food

    @pytest.mark.parametrize(
        "args,expected",
        [
            (
                "1, name, 01/6/55, 1:55",
                {
                    "id": "1",
                    "name": "name",
                    "date": datetime(day=1, month=6, year=55),
                    "time": time(hour=1, minute=55),
                },
            ),
            (
                "1, 01/6/55, name, 1:55",
                {
                    "id": "1",
                    "name": "name",
                    "date": datetime(day=1, month=6, year=55),
                    "time": time(hour=1, minute=55),
                },
            ),
            (
                "1, name, 01/6/55",
                {
                    "id": "1",
                    "name": "name",
                    "date": datetime(day=1, month=6, year=55),
                },
            ),
            (
                "1, name, 16:55",
                {
                    "id": "1",
                    "name": "name",
                    "time": time(hour=16, minute=55),
                },
            ),
            ("1, name", {"id": "1", "name": "name"}),
        ],
    )
    def test_parse_args_given_valid_args(self, args, expected):
        assert UpdateCommand.parse_args(args) == expected

    @pytest.mark.parametrize(
        "args",
        [
            "1" "1, name, name2",
            "1, 16:55, 16:55",
            "1, aa/bb",
            "1, aa:bb",
            "1, name, 01/6/55, 1:55, extra",
        ],
    )
    def test_parse_args_given_invalid_args(self, args):
        with pytest.raises(InvalidArgs):
            UpdateCommand.parse_args(args)

    def test_execute_args_given_valid_args(self):
        random_string = get_random_string(20)
        self.Food.insert(name=random_string).execute()
        inserted_id = (
            self.Food.select().where(self.Food.name == random_string).get().id
        )
        new_name = "new_string"

        UpdateCommand.execute(f"{inserted_id}, {new_name}")

        assert self.Food.get_by_id(inserted_id).name == new_name
