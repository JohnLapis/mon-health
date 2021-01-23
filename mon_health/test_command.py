import random
from datetime import datetime, time

import pytest

from .command import (
    CommandNotFound,
    FindCommand,
    HelpCommand,
    IdFieldNotFound,
    InsertCommand,
    InvalidId,
    NameFieldNotFound,
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
            ("  a  , b  ", ["a", "b"]),
            (" z,a  ", ["a", "z"]),
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
                "n 'hotdog'",
                lambda Food: (
                    Food.select()
                    .where(Food.name == "hotdog")
                    .order_by(Food.date.asc(), Food.time.asc())
                    .limit(-1)
                    .dicts()
                ),
            ),
            (
                "D toDAY",
                lambda Food: (
                    Food.select()
                    .where(Food.date == datetime.now().date())
                    .order_by(Food.date.asc(), Food.time.asc())
                    .limit(-1)
                    .dicts()
                ),
            ),
            (
                "soRt date | all",
                lambda Food: (
                    Food.select()
                    .where(True)
                    .order_by(Food.date.asc())
                    .limit(-1)
                    .dicts()
                ),
            ),
            (
                "LimIT 5 | date,time",
                lambda Food: (
                    Food.select(Food.date, Food.time)
                    .where(True)
                    .order_by(Food.date.asc(), Food.time.asc())
                    .limit(5)
                    .dicts())
             ),
            (
                "d 1/01 Time 5h    sort  date LImit 1 | name",
                lambda Food: (
                    Food.select(Food.name)
                    .where(
                        (Food.date == datetime(day=1, month=1, year=now().year))
                        & Food.time.between(
                            time(hour=5, minute=00), time(hour=5, minute=59)
                        )
                    )
                    .order_by(Food.date.asc())
                    .limit(1)
                    .dicts()
                ),
            ),
        ],
    )
    def test_parse_args_given_valid_args(self, args, expected):
        query = FindCommand.parse_args(args)
        expected_query = expected(self.Food)
        assert query.sql() == expected_query.sql()


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
                "iD 1 n `foo` d 1/06 t 1:55",
                {
                    "id": 1,
                    "name": "foo",
                    "date": datetime(day=1, month=6, year=now().year),
                    "time": time(hour=1, minute=55),
                },
            ),
            (
                "iD 1 D 01/6/55 naMe `foo` t 1:55",
                {
                    "id": 1,
                    "name": "foo",
                    "date": datetime(day=1, month=6, year=55),
                    "time": time(hour=1, minute=55),
                },
            ),
            (
                "id 1 name `foo` d 12",
                {
                    "id": 1,
                    "name": "foo",
                    "date": datetime(day=12, month=now().month, year=now().year),
                },
            ),
            (
                "id 1 name `foo` t 16h",
                {
                    "id": 1,
                    "name": "foo",
                    "time": time(hour=16, minute=0),
                },
            ),
            ("id 1 name `foo`", {"id": 1, "name": "foo"}),
        ],
    )
    def test_parse_args_given_valid_args(self, args, expected):
        assert UpdateCommand.parse_args(args) == expected

    @pytest.mark.parametrize(
        "args,error",
        [
            ("", IdFieldNotFound),
            ("name '55'", IdFieldNotFound),
            ("Id foo 16:55", InvalidId),
            ("iD 1 daTe 11/11", NameFieldNotFound),
        ],
    )
    def test_parse_args_given_invalid_args(self, args, error):
        with pytest.raises(error):
            UpdateCommand.parse_args(args)

    def test_execute_args_given_valid_args(self):
        random_string = get_random_string(20)
        self.Food.insert(name=random_string).execute()
        inserted_id = (
            self.Food.select().where(self.Food.name == random_string).get().id
        )
        new_name = "new_string"

        UpdateCommand.execute(f"id {inserted_id} name '{new_name}'")

        assert self.Food.get_by_id(inserted_id).name == new_name
