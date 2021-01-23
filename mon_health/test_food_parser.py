from datetime import datetime, time

import peewee
import pytest

from .food_parser import (
    Food,
    FoodParser,
    InvalidExpression,
    InvalidLimit,
    InvalidName,
    InvalidColumn,
    InvalidValue,
    KeywordNotFound,
)


def now():
    return datetime.now()


def isExpr(obj):
    return isinstance(obj, peewee.Expression)


def isField(obj):
    return issubclass(obj.__class__, peewee.Field)


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


@pytest.mark.parametrize(
    "args,expected",
    [
        (
            'N "name" datE 1/01 t 5h sort date,name l 1',
            {
                "where_clause": (
                    (Food.name == "name")
                    & (Food.date == datetime(day=1, month=1, year=now().year))
                    & Food.time.between(
                        time(hour=5, minute=0),
                        time(hour=5, minute=59),
                    )
                ),
                "sort_clause": [Food.date.asc(), Food.name.asc()],
                "limit_clause": 1,
            },
        ),
        # the following 4 cases shows order doesn't matter for where_clause
        (
            "name `name` time 5:05 date 12/12",
            {
                "where_clause": (
                    (Food.name == "name")
                    & (Food.date == datetime(day=12, month=12, year=now().year))
                    & (Food.time == time(hour=5, minute=5))
                ),
                "sort_clause": [],
                "limit_clause": -1,
            },
        ),
        (
            "time 5:05 name `name` date 12/12",
            {
                "where_clause": (
                    (Food.name == "name")
                    & (Food.date == datetime(day=12, month=12, year=now().year))
                    & (Food.time == time(hour=5, minute=5))
                ),
                "sort_clause": [],
                "limit_clause": -1,
            },
        ),
        (
            "date 12/12 time 5:05 name `name`",
            {
                "where_clause": (
                    (Food.name == "name")
                    & (Food.date == datetime(day=12, month=12, year=now().year))
                    & (Food.time == time(hour=5, minute=5))
                ),
                "sort_clause": [],
                "limit_clause": -1,
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
            },
        ),
        (
            # shows where_clause is optional
            "sort time limit 5",
            {
                "where_clause": True,
                "sort_clause": [Food.time.asc()],
                "limit_clause": 5,
            },
        ),
        (
            "limit 5",
            {
                "where_clause": True,
                "sort_clause": [],
                "limit_clause": 5,
            },
        ),
        (
            "date today",
            {
                "where_clause": Food.date == now().date(),
                "sort_clause": [],
                "limit_clause": -1,
            },
        ),
        (
            "",
            {
                "where_clause": True,
                "sort_clause": [],
                "limit_clause": -1,
            },
        ),
    ],
)
def test_parse_given_valid_args(args, expected):
    parser = FoodParser(args)
    parser.parse()

    assert compare_nested_exprs(parser.where_clause, expected["where_clause"])
    assert parser.sort_clause == expected["sort_clause"]
    assert parser.limit_clause == expected["limit_clause"]


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
def test_parse_given_invalid_args(args, error, invalid_value):
    parser = FoodParser(args)
    with pytest.raises(error, match=rf".+?'{invalid_value}'.+"):
        parser.parse()


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
def test_search_keyword(string, expr_name, expected):
    parser = FoodParser("")
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
def test_ends_with_keyword():
    pass


@pytest.mark.parametrize(
    "args,expected",
    [
        ('"hotdog"', Food.name == "hotdog"),
        ("`hotdog`", Food.name == "hotdog"),
        ("'hotdog'", Food.name == "hotdog"),
        ("'  hotdog  '", Food.name == "  hotdog  "),
    ],
)
def test_parse_name_given_valid_args(args, expected):
    parser = FoodParser("")
    parser.parse_name(args)
    assert compare_nested_exprs(parser.where_clause, expected)


@pytest.mark.parametrize(
    "args",
    [
        "''",
        "hotdog",  # no quotes
        "`hotdog",  # single quote
        "'hotdog\"",  # beginning and ending with different quotes
    ],
)
def test_parse_name_given_invalid_args(args):
    parser = FoodParser("")
    with pytest.raises(InvalidName):
        parser.parse_name(args)


@pytest.mark.parametrize(
    "args,expected",
    [
        ("today", Food.date == datetime.now().date()),
        ("toDAY", Food.date == datetime.now().date()),
        ("1", Food.date == datetime(day=1, month=now().month, year=now().year)),
        ("18", Food.date == datetime(day=18, month=now().month, year=now().year)),
        ("18/5", Food.date == datetime(day=18, month=5, year=now().year)),
        ("1/5/2000", Food.date == datetime(day=1, month=5, year=2000)),
    ],
)
def test_parse_date_given_valid_args(args, expected):
    parser = FoodParser("")
    parser.parse_date(args)
    assert compare_nested_exprs(parser.where_clause, expected)


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
def test_parse_time_given_valid_args(args, expected):
    parser = FoodParser("")
    parser.parse_time(args)
    assert compare_nested_exprs(parser.where_clause, expected)


@pytest.mark.parametrize(
    "args,expected",
    [
        ("date", [Food.date.asc()]),
        ("-date", [Food.date.desc()]),
        ("-date,-name,time", [Food.date.desc(), Food.name.desc(), Food.time.asc()]),
        ("date,-name", [Food.date.asc(), Food.name.desc()]),
    ],
)
def test_parse_sort_given_valid_args(args, expected):
    parser = FoodParser("")
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
def test_parse_sort_given_invalid_args(args):
    parser = FoodParser("")
    with pytest.raises(InvalidColumn):
        parser.parse_sort(args)


@pytest.mark.parametrize("args,expected", [("5", 5), ("0", 0)])
def test_parse_limit_given_valid_args(args, expected):
    parser = FoodParser("")
    parser.parse_limit(args)
    assert parser.limit_clause == expected


@pytest.mark.parametrize("args", ["a", "", "-4", "5.0"])
def test_parse_limit_given_invalid_args(args):
    parser = FoodParser("")
    with pytest.raises(InvalidLimit):
        parser.parse_limit(args)
