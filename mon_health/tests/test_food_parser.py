import os
from datetime import date, datetime, time

import pytest
from peewee import (
    CharField,
    DateField,
    Expression,
    Field,
    Model,
    SqliteDatabase,
    TimeField,
)

from mon_health.food_parser import (
    FoodParser,
    InvalidColumn,
    InvalidExpression,
    InvalidId,
    InvalidLimit,
    InvalidName,
    InvalidValue,
    KeywordNotFound,
)

TEST_DB_PATH = "test_food_parser.db"
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


def teardown_db():
    os.remove(TEST_DB_PATH)


def now():
    return datetime.now()


def isExpr(obj):
    return isinstance(obj, Expression)


def isField(obj):
    return issubclass(obj.__class__, Field)


def compare_rhs_of_between_op(rhs1, rhs2):
    assert rhs1.nodes[0] == rhs2.nodes[0]
    assert rhs1.nodes[1].sql == rhs2.nodes[1].sql
    assert rhs1.nodes[2] == rhs2.nodes[2]
    return True


def compare_nested_exprs(expr1, expr2):
    if isField(expr1) or isField(expr2):
        return expr1 is expr2
    if not isExpr(expr1) or not isExpr(expr2):
        assert not isExpr(expr1) and not isExpr(expr2)
        return expr1 == expr2

    assert compare_nested_exprs(expr1.lhs, expr2.lhs)
    assert expr1.op == expr2.op
    if expr1.op == "BETWEEN":
        assert compare_rhs_of_between_op(expr1.rhs, expr2.rhs)
    else:
        assert compare_nested_exprs(expr1.rhs, expr2.rhs)
    return True


class TestFoodParser:
    @classmethod
    def teardown_class(cls):
        teardown_db()

    @pytest.mark.parametrize(
        "args,expected",
        [
            (
                'id 1 N "name" datE 1/01 t 5h sort date,name l 1 returNinG name,time',
                {
                    "where_clause": (
                        (Food.id == 1)
                        & (Food.name == "name")
                        & (Food.date == date(day=1, month=1, year=now().year))
                        & Food.time.between(
                            time(hour=5, minute=0),
                            time(hour=5, minute=59),
                        )
                    ),
                    "sort_clause": [Food.date.asc(), Food.name.asc()],
                    "limit_clause": 1,
                    "returning_clause": [Food.name, Food.time],
                },
            ),
            # the following 4 cases shows order doesn't matter for where_clause
            (
                "name `name` time 5:05 date 12/12 returning ALL",
                {
                    "where_clause": (
                        (Food.name == "name")
                        & (Food.date == date(day=12, month=12, year=now().year))
                        & (Food.time == time(hour=5, minute=5))
                    ),
                    "sort_clause": [],
                    "limit_clause": -1,
                    "returning_clause": [],
                },
            ),
            (
                "time 5:05 name `name` date 12/12",
                {
                    "where_clause": (
                        (Food.name == "name")
                        & (Food.date == date(day=12, month=12, year=now().year))
                        & (Food.time == time(hour=5, minute=5))
                    ),
                    "sort_clause": [],
                    "limit_clause": -1,
                    "returning_clause": [],
                },
            ),
            (
                "date 12/12 time 5:05 name `name`",
                {
                    "where_clause": (
                        (Food.name == "name")
                        & (Food.date == date(day=12, month=12, year=now().year))
                        & (Food.time == time(hour=5, minute=5))
                    ),
                    "sort_clause": [],
                    "limit_clause": -1,
                    "returning_clause": [],
                },
            ),
            (
                "t 5h n 'name'",
                {
                    "where_clause": (
                        (Food.name == "name")
                        & Food.time.between(
                            time(hour=5, minute=00), time(hour=5, minute=59)
                        )
                    ),
                    "sort_clause": [],
                    "limit_clause": -1,
                    "returning_clause": [],
                },
            ),
            (
                # shows where_clause is optional
                "sort time limit 5",
                {
                    "where_clause": True,
                    "sort_clause": [Food.time.asc()],
                    "limit_clause": 5,
                    "returning_clause": [],
                },
            ),
            (
                "limit 5",
                {
                    "where_clause": True,
                    "sort_clause": [],
                    "limit_clause": 5,
                    "returning_clause": [],
                },
            ),
            (
                "date today",
                {
                    "where_clause": Food.date == now().date(),
                    "sort_clause": [],
                    "limit_clause": -1,
                    "returning_clause": [],
                },
            ),
            (
                "| time,name",
                {
                    "where_clause": True,
                    "sort_clause": [],
                    "limit_clause": -1,
                    "returning_clause": [Food.time, Food.name],
                },
            ),
            (
                "iD 66",
                {
                    "where_clause": Food.id == 66,
                    "sort_clause": [],
                    "limit_clause": -1,
                    "returning_clause": [],
                },
            ),
            (
                "",
                {
                    "where_clause": True,
                    "sort_clause": [],
                    "limit_clause": -1,
                    "returning_clause": [],
                },
            ),
        ],
    )
    def test_parse_given_valid_args(self, args, expected):
        parser = FoodParser(Food)
        parser.parse(args)

        assert compare_nested_exprs(parser.where_clause, expected["where_clause"])
        assert parser.sort_clause == expected["sort_clause"]
        assert parser.limit_clause == expected["limit_clause"]
        assert parser.returning_clause == expected["returning_clause"]

    @pytest.mark.parametrize(
        "arg_list,expected_attrs",
        [
            (
                [
                    'id 1 N "name1" datE 1/01 t 5h sort date,name returNinG name,time',
                    'id 3 N "name2" t 6:05 sort -date l 2 returNinG All',
                ],
                [
                    {
                        "where_clause": (
                            (Food.id == 1)
                            & (Food.name == "name1")
                            & (Food.date == date(day=1, month=1, year=now().year))
                            & Food.time.between(
                                time(hour=5, minute=0),
                                time(hour=5, minute=59),
                            )
                        ),
                        "sort_clause": [Food.date.asc(), Food.name.asc()],
                        "limit_clause": -1,
                        "returning_clause": [Food.name, Food.time],
                        "id": 1,
                        "name": "name1",
                        "date": date(day=1, month=1, year=now().year),
                        "time": time(hour=5, minute=0),
                        "columns": ["name", "time"],
                    },
                    {
                        "where_clause": (
                            (Food.id == 1)
                            & (Food.name == "name1")
                            & (Food.date == date(day=1, month=1, year=now().year))
                            & Food.time.between(
                                time(hour=5, minute=0),
                                time(hour=5, minute=59),
                            )
                            & (Food.id == 3)
                            & (Food.name == "name2")
                            & (Food.time == time(hour=6, minute=5))
                        ),  # altered
                        "sort_clause": [Food.date.desc()],  # altered
                        "limit_clause": 2,  # altered
                        "returning_clause": [],  # altered
                        "id": 3,  # altered
                        "name": "name2",  # altered
                        "date": date(day=1, month=1, year=now().year),
                        "time": time(hour=6, minute=5),  # altered
                        "columns": [],  # altered
                    },
                ],
            ),
        ],
    )
    def test_parse_given_reset_false(self, arg_list, expected_attrs):
        assert len(arg_list) == len(expected_attrs)
        parser = FoodParser(Food)
        for args, expected in zip(arg_list, expected_attrs):
            parser.parse(args, reset=False)
            assert compare_nested_exprs(
                parser.where_clause, expected["where_clause"]
            )
            assert parser.sort_clause == expected["sort_clause"]
            assert parser.limit_clause == expected["limit_clause"]
            assert parser.returning_clause == expected["returning_clause"]
            assert parser.id == expected["id"]
            assert parser.name == expected["name"]
            assert parser.date == expected["date"]
            assert parser.time == expected["time"]
            assert parser.columns == expected["columns"]

    @pytest.mark.parametrize(
        "args,error,invalid_value",
        # fmt: off
        [
            ("date",                  InvalidValue,      ""),
            ("date not_a_date",       InvalidValue,      "not_a_date"),
            ("date not_a_date 05/05", InvalidValue,      "not_a_date"),
            ("date date 10/10",       InvalidValue,      "date"),
            ("time date 18/5",        InvalidValue,      "date"),
            ("date foo 10:10",        InvalidValue,      "foo"),
            ("foo",                   InvalidExpression, "foo"),
            ("foo 10:10",             InvalidExpression, "foo 10:10"),
            ("foo date 10/10",        InvalidExpression, "foo"),
            ("foo bar date 10/10",    InvalidExpression, "foo bar"),
            ("time 12:59 foo",        InvalidExpression, "foo"),
            ("date 18/5 date 18/5",   InvalidExpression, "date 18/5"),
            ("date 18/5 date",        InvalidExpression, "date"),
            ("date 18/5 18/5",        InvalidExpression, "18/5"),
           ],
        # fmt: on
    )
    def test_parse_given_invalid_args(self, args, error, invalid_value):
        parser = FoodParser(Food)
        with pytest.raises(error, match=rf".+?'{invalid_value}'.+"):
            parser.parse(args)

    @pytest.mark.parametrize(
        "string,expr_name,expected",
        [
            (" date sort ", "sort", None),
            (" dATe sort ", "date", "dATe"),
            (" tIme date ", "date", None),
            (" tiME dAte ", "time", "tiME"),
            (" s date ", "date", None),
            (" s date ", "sort", "s"),
            (" n time ", "time", None),
            (" N time ", "name", "N"),
        ],
    )
    def test_search_keyword(self, string, expr_name, expected):
        parser = FoodParser(Food)
        for expr in parser.exprs:
            if expr["name"] == expr_name:
                pattern = expr["keyword_pattern"]

        if expected is None:
            with pytest.raises(KeywordNotFound):
                parser.search_keyword(pattern, string)
        else:
            match = parser.search_keyword(pattern, string)
            assert match.matched == expected

    @pytest.mark.skip
    def test_ends_with_keyword(self):
        pass

    def test_reset_attributes(self):
        parser = FoodParser(Food)
        parser.where_clause_exprs = ["foo"]
        parser.id = 1
        parser.name = "name"
        parser.date = "date"
        parser.time = "time"
        parser.sort_clause = ["foo"]
        parser.limit_clause = 999
        parser.columns = ["foo"]
        parser.returning_clause = ["foo"]

        parser.reset_attributes()

        assert parser.id is None
        assert parser.name is None
        assert parser.date is None
        assert parser.time is None
        assert parser.sort_clause == []
        assert parser.limit_clause == -1
        assert parser.columns == []
        assert parser.returning_clause == []

    @pytest.mark.parametrize(
        "args,expected",
        [
            ("4", Food.id == 4),
            ("44", Food.id == 44),
        ],
    )
    def test_parse_id_given_valid_args(self, args, expected):
        parser = FoodParser(Food)
        parser.parse_id(args)
        assert compare_nested_exprs(parser.where_clause, expected)
        assert parser.id == expected.rhs

    @pytest.mark.parametrize("args", ["", "a", "-4", "0.5"])
    def test_parse_id_given_invalid_args(self, args):
        parser = FoodParser(Food)
        with pytest.raises(InvalidId):
            parser.parse_id(args)

    @pytest.mark.parametrize(
        "args,expected",
        [
            ('"hotdog"', Food.name == "hotdog"),
            ("`hotdog`", Food.name == "hotdog"),
            ("'hotdog'", Food.name == "hotdog"),
            ("'  hotdog  '", Food.name == "  hotdog  "),
        ],
    )
    def test_parse_name_given_valid_args(self, args, expected):
        parser = FoodParser(Food)
        parser.parse_name(args)
        assert compare_nested_exprs(parser.where_clause, expected)
        assert parser.name == expected.rhs

    @pytest.mark.parametrize(
        "args",
        [
            "''",
            "hotdog",  # no quotes
            "`hotdog",  # single quote
            "'hotdog\"",  # beginning and ending with different quotes
        ],
    )
    def test_parse_name_given_invalid_args(self, args):
        parser = FoodParser(Food)
        with pytest.raises(InvalidName):
            parser.parse_name(args)

    @pytest.mark.parametrize(
        "args,expected",
        [
            ("today", Food.date == datetime.now().date()),
            ("toDAY", Food.date == datetime.now().date()),
            ("1", Food.date == date(day=1, month=now().month, year=now().year)),
            ("18", Food.date == date(day=18, month=now().month, year=now().year)),
            ("18/5", Food.date == date(day=18, month=5, year=now().year)),
            ("1/5/2000", Food.date == date(day=1, month=5, year=2000)),
        ],
    )
    def test_parse_date_given_valid_args(self, args, expected):
        parser = FoodParser(Food)
        parser.parse_date(args)
        assert compare_nested_exprs(parser.where_clause, expected)
        assert parser.date == expected.rhs

    @pytest.mark.parametrize(
        "args,expected",
        [
            (
                "18h",
                Food.time.between(
                    time(hour=18, minute=00),
                    time(hour=18, minute=59),
                ),
            ),
            ("18:55", Food.time == time(hour=18, minute=55)),
        ],
    )
    def test_parse_time_given_valid_args(self, args, expected):
        parser = FoodParser(Food)
        parser.parse_time(args)
        assert compare_nested_exprs(parser.where_clause, expected)
        if isinstance(expected.rhs, time):
            assert parser.time == expected.rhs
        else:
            assert parser.time == expected.rhs.nodes[0]

    @pytest.mark.parametrize(
        "args,expected",
        [
            ("date", [Food.date.asc()]),
            ("-date", [Food.date.desc()]),
            (
                "-date,-name,time",
                [Food.date.desc(), Food.name.desc(), Food.time.asc()],
            ),
            ("date,-name", [Food.date.asc(), Food.name.desc()]),
        ],
    )
    def test_parse_sort_given_valid_args(self, args, expected):
        parser = FoodParser(Food)
        parser.parse_sort(args)
        assert parser.sort_clause == expected

    @pytest.mark.parametrize(
        "args",
        [
            "",
            "time,",  # ends with comma
            "   time",
            "time  ",
            "zzzz",  # invalid Food field
        ],
    )
    def test_parse_sort_given_invalid_args(self, args):
        parser = FoodParser(Food)
        with pytest.raises(InvalidColumn):
            parser.parse_sort(args)

    @pytest.mark.parametrize("args,expected", [("5", 5), ("0", 0)])
    def test_parse_limit_given_valid_args(self, args, expected):
        parser = FoodParser(Food)
        parser.parse_limit(args)
        assert parser.limit_clause == expected

    @pytest.mark.parametrize("args", ["a", "", "-4", "5.0"])
    def test_parse_limit_given_invalid_args(self, args):
        parser = FoodParser(Food)
        with pytest.raises(InvalidLimit):
            parser.parse_limit(args)

    @pytest.mark.parametrize(
        "args,expected",
        [
            ("", []),
            ("all", []),
            ("name", [Food.name]),
            ("name,time", [Food.name, Food.time]),
        ],
    )
    def test_parse_returning_given_valid_args(self, args, expected):
        parser = FoodParser(Food)
        parser.parse_returning(args)
        assert parser.returning_clause == expected
        assert parser.columns == [col.name for col in expected]

    @pytest.mark.parametrize(
        "args",
        [
            "time,",  # ends with comma
            "   time",
            "time  ",
            "zzzz",  # invalid Food field
        ],
    )
    def test_parse_returning_given_invalid_args(self, args):
        parser = FoodParser(Food)
        with pytest.raises(InvalidColumn):
            parser.parse_returning(args)
