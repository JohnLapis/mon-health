import os
import random
from datetime import datetime, time

import pytest
from peewee import CharField, DateField, Model, SqliteDatabase, TimeField

from mon_health.command import (
    CommandNotFound,
    DeleteCommand,
    ExitCommand,
    FindCommand,
    HelpCommand,
    IdFieldNotFound,
    InsertCommand,
    NameFieldNotFound,
    UpdateCommand,
    parse_query,
    setup_commands,
)


@pytest.fixture(scope="class")
def Food():
    TEST_DB_PATH = "test_command.db"
    TEST_DB = SqliteDatabase(TEST_DB_PATH)

    class BaseModel(Model):
        class Meta:
            database = TEST_DB

    class Food(BaseModel):
        name = CharField(max_length=20)
        time = TimeField(default=lambda: time(hour=now().hour, minute=now().minute))
        date = DateField(default=lambda: now().date())

    tables = {table.__name__.lower(): table for table in [Food]}
    TEST_DB.create_tables(tables.values())
    setup_commands(tables)
    yield Food
    os.remove(TEST_DB_PATH)


def get_random_string(length):
    letters = "abcdefghijklmnopqrstuvwxyz"
    return "".join(random.choice(letters) for i in range(length))


def now():
    return datetime.now()


class TestHelpCommand:
    @classmethod
    def setup_class(cls):
        class TestCommand:
            description = "Test."

        COMMAND_TABLE = {
            "test1": TestCommand,
            "test2": TestCommand,
        }
        db_tables = {"food": ""}
        setup_commands(db_tables, COMMAND_TABLE)

    @pytest.mark.parametrize(
        "args,expected",
        [
            ("", ["test1               Test.", "test2               Test."]),
            ("test1", ["test1               Test."]),
        ],
    )
    def test_execute_given_valid_args(self, args, expected):
        assert HelpCommand.execute(args) == expected

    def test_execute_given_invalid_args(self):
        with pytest.raises(CommandNotFound):
            HelpCommand.execute("nonexistent command")


class TestInsertCommand:
    @pytest.mark.parametrize(
        "args,expected",
        [
            ("a", lambda Food: Food.insert_many([{"name": "a"}])),
            (
                "a, b  ",
                lambda Food: Food.insert_many([{"name": "a"}, {"name": "b"}]),
            ),
            (
                "  a  , b  ",
                lambda Food: Food.insert_many([{"name": "a"}, {"name": "b"}]),
            ),
            (
                " z,a  ",
                lambda Food: Food.insert_many([{"name": "a"}, {"name": "z"}]),
            ),
        ],
    )
    def test_parse_args_given_valid_args(self, args, expected, Food):
        query = InsertCommand.parse_args(args)
        expected_query = expected(Food)
        assert query.sql() == expected_query.sql()

    def test_execute_given_valid_args(self, Food):
        random_string = get_random_string(20)
        InsertCommand.execute(random_string)
        inserted_id = Food.select().where(Food.name == random_string).get().id
        assert Food.delete_by_id(inserted_id) == 1


class TestFindCommand:
    @pytest.mark.parametrize(
        "args,expected",
        [
            (
                "n 'hotdog'",
                (
                    lambda Food: (
                        Food.select()
                        .where(Food.name == "hotdog")
                        .order_by(Food.date.asc(), Food.time.asc())
                        .limit(-1)
                        .dicts()
                    ),
                    ["id", "name", "time", "date"],
                ),
            ),
            (
                "D toDAY",
                (
                    lambda Food: (
                        Food.select()
                        .where(Food.date == datetime.now().date())
                        .order_by(Food.date.asc(), Food.time.asc())
                        .limit(-1)
                        .dicts()
                    ),
                    ["id", "name", "time", "date"],
                ),
            ),
            (
                "soRt date | all",
                (
                    lambda Food: (
                        Food.select()
                        .where(True)
                        .order_by(Food.date.asc())
                        .limit(-1)
                        .dicts()
                    ),
                    ["id", "name", "time", "date"],
                ),
            ),
            (
                "LimIT 5 | date,time",
                (
                    lambda Food: (
                        Food.select(Food.date, Food.time)
                        .where(True)
                        .order_by(Food.date.asc(), Food.time.asc())
                        .limit(5)
                        .dicts()
                    ),
                    ["date", "time"],
                ),
            ),
            (
                "d 1/01 Time 5h    sort  date LImit 1 | name",
                (
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
                    ["name"],
                ),
            ),
        ],
    )
    def test_parse_args_given_valid_args(self, args, expected, Food):
        query, columns = FindCommand.parse_args(args)
        expected_query = expected[0](Food)
        assert query.sql() == expected_query.sql()
        assert columns == expected[1]


class TestUpdateCommand:
    @pytest.mark.parametrize(
        "args,expected",
        [
            (
                "iD 1 n `foo` d 1/06 t 1:55",
                lambda Food: Food.replace(
                    **{
                        "id": 1,
                        "name": "foo",
                        "date": datetime(day=1, month=6, year=now().year),
                        "time": time(hour=1, minute=55),
                    }
                ),
            ),
            (
                "iD 1 D 01/6/55 naMe `foo` t 1:55",
                lambda Food: Food.replace(
                    **{
                        "id": 1,
                        "name": "foo",
                        "date": datetime(day=1, month=6, year=55),
                        "time": time(hour=1, minute=55),
                    },
                ),
            ),
            (
                "id 1 name `foo` d 12",
                lambda Food: Food.replace(
                    **{
                        "id": 1,
                        "name": "foo",
                        "date": datetime(day=12, month=now().month, year=now().year),
                    },
                ),
            ),
            (
                "id 1 name `foo` t 16h",
                lambda Food: Food.replace(
                    **{
                        "id": 1,
                        "name": "foo",
                        "time": time(hour=16, minute=0),
                    },
                ),
            ),
            (
                "id 1 name `foo`",
                lambda Food: Food.replace(**{"id": 1, "name": "foo"}),
            ),
        ],
    )
    def test_parse_args_given_valid_args(self, args, expected, Food):
        query = UpdateCommand.parse_args(args)
        expected_query = expected(Food)
        assert query.sql() == expected_query.sql()

    @pytest.mark.parametrize(
        "args,error",
        [
            ("", IdFieldNotFound),
            ("name '55'", IdFieldNotFound),
            ("iD 1 daTe 11/11", NameFieldNotFound),
        ],
    )
    def test_parse_args_given_invalid_args(self, args, error):
        with pytest.raises(error):
            UpdateCommand.parse_args(args)

    def test_execute_given_valid_args(self, Food):
        random_string = get_random_string(20)
        Food.insert(name=random_string).execute()
        inserted_id = Food.select().where(Food.name == random_string).get().id
        new_name = "new_string"

        UpdateCommand.execute(f"id {inserted_id} name '{new_name}'")

        assert Food.get_by_id(inserted_id).name == new_name


class TestDeleteCommand:
    @pytest.mark.parametrize(
        "args,expected",
        [
            (
                "iD 1 n `foo` d 1/06 t 1:55",
                lambda Food: (
                    Food.delete().where(
                        (Food.id == 1)
                        & (Food.name == "foo")
                        & (Food.date == datetime(day=1, month=6, year=now().year))
                        & (Food.time == time(hour=1, minute=55))
                    )
                ),
            ),
            (
                "id 1 name `foo`",
                lambda Food: (
                    Food.delete().where((Food.id == 1) & (Food.name == "foo"))
                ),
            ),
        ],
    )
    def test_parse_args_given_valid_args(self, args, expected, Food):
        query = DeleteCommand.parse_args(args)
        expected_query = expected(Food)
        assert query.sql() == expected_query.sql()

    def test_execute_given_valid_args(self, Food):
        random_string = get_random_string(20)
        Food.insert(name=random_string).execute()
        inserted_id = Food.select().where(Food.name == random_string).get().id

        DeleteCommand.execute(f"name '{random_string}'")

        query = Food.select().where(Food.id == inserted_id).execute()
        assert list(query) == []


class TestExitCommand:
    @pytest.mark.parametrize("args", ["", "a"])
    def test_execute_given_valid_args(self, args):
        assert ExitCommand.execute(args) == []


@pytest.mark.parametrize(
    "string,expected",
    [
        ("a", ("a", "")),
        ("a b", ("a", "b")),
        ("a    $   ", ("a", "$")),
        ("a 2       b", ("a", "2       b")),
    ],
)
def test_parse_query_given_valid_input(string, expected):
    assert parse_query(string) == expected


@pytest.mark.parametrize("string", ["", " "])
def test_parse_query_given_invalid_input(string):
    with pytest.raises(CommandNotFound):
        parse_query(string)
