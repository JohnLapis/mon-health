from datetime import datetime, time

import pytest

from .food_parser import Food, FoodParser


def now():
    return datetime.now()


@pytest.mark.parametrize(
    "args,expected",
    [
        ("hotdog; ", {"where_clause": Food.name == "hotdog"}),
        (
            "hotdog   ;    today",
            {
                "where_clause": (Food.name == "hotdog")
                & (Food.date == datetime.now().date())
            },
        ),
        ("toDAY", {"where_clause": datetime.now().date()}),
        (
            "18",
            {
                "where_clause": (
                    Food.date == datetime(day=1, month=now().month, year=now().year)
                )
            },
        ),
        (
            "18/5",
            {
                "where_clause": (
                    Food.date == datetime(day=1, month=5, year=now().year)
                )
            },
        ),
        (
            "18/5/2000",
            {"where_clause": (Food.date == datetime(day=1, month=5, year=2000))},
        ),
        (
            "18h",
            {
                "where_clause": (
                    Food.time.between(
                        time(hour=18, minute=00), time(hour=18, minute=59)
                    )
                )
            },
        ),
        (
            "18:55",
            {"where_clause": (Food.time == time(hour=18, minute=55))},
        ),
        ("sort date", {"sorting_clause": Food.date}),
        ("order BY -date", {"sorting_clause": Food.date.desc()}),
        ("LIMIT 5", {"limit_clause": "5"}),
        (
            "food   ; 1/01 5h    sort  date LImit 1",
            {
                "where_clause": (
                    (Food.name == "food")
                    & (Food.date == datetime(day=1, month=1, year=now().year))
                    & Food.time.between(
                        time(hour=5, minute=00), time(hour=5, minute=59)
                    )
                ),
                "sorting_clause": Food.date,
                "limit_clause": "1",
            },
        ),
    ],
)
def test_parse_args_given_valid_args(args, expected):
    parser = FoodParser(args)
    parser.parse()

    clauses = ["where_clause", "sorting_clause", "limit_clause"]
    for key in expected:
        assert bool(getattr(parser, key) == expected[key])
        clauses.remove(key)

    for clause in clauses:
        assert getattr(parser, clause) is None
