from datetime import date, datetime, time

import pytest

from .utils import (
    InvalidDate,
    InvalidTime,
    convert_to_date,
    convert_to_time,
    format_rows,
    pad_row_values,
)


def now():
    return datetime.now()


@pytest.mark.parametrize(
    "string,expected",
    [
        ("1", date(day=1, month=now().month, year=now().year)),
        ("01", date(day=1, month=now().month, year=now().year)),
        ("12/1", date(day=12, month=1, year=now().year)),
        ("1/01", date(day=1, month=1, year=now().year)),
        ("1/12", date(day=1, month=12, year=now().year)),
        ("1/12/1920", date(day=1, month=12, year=1920)),
    ],
)
def test_convert_to_date_given_valid_input(string, expected):
    assert convert_to_date(string) == expected


@pytest.mark.parametrize("string", ["", "a", "1//", "1/0t", "6/6/2020/20"])
def test_convert_to_date_given_invalid_input(string):
    with pytest.raises(InvalidDate):
        convert_to_date(string)


@pytest.mark.parametrize(
    "string,expected",
    [
        ("1", time(hour=1, minute=0)),
        ("01", time(hour=1, minute=0)),
        ("12:1", time(hour=12, minute=1)),
        ("1:01", time(hour=1, minute=1)),
    ],
)
def test_convert_to_time_given_valid_input(string, expected):
    assert convert_to_time(string) == expected


@pytest.mark.parametrize("string", ["", "a", "1:a", "1:1:1"])
def test_convert_to_time_given_invalid_input(string):
    with pytest.raises(InvalidTime):
        convert_to_time(string)


@pytest.mark.parametrize(
    "rows,cols,expected",
    [
        # fmt: off
        (
            [
                {"name": "name",        "date": date(day=1, month=1, year=21)},
                {"name": "name big",    "date": date(day=5, month=5, year=201)},
                {"name": "name bigger", "date": date(day=7, month=7, year=2001)},
            ],
            ["name", "date"],
            [
                "NAME        | DATE      ",
                "------------+-----------",
                "name        | 01/01/21  ",
                "name big    | 05/05/201 ",
                "name bigger | 07/07/2001",
            ],
        ),
        (
            [
                {"Id": 1,   "date": "whatever", "tIme": time(hour=11, minute=11)},
                {"Id": 10,  "date": "whatever", "tIme": time(hour=22, minute=22)},
                {"Id": 100, "date": "whatever", "tIme": time(hour=13, minute=13)},
            ],
            ["Id", "tIme"],
            [
                "ID  | TIME ",
                "----+------",
                "1   | 11:11",
                "10  | 22:22",
                "100 | 13:13",
            ],
        ),
        # fmt: on
        (
            [
                {
                    "name": "name",
                    "date": date(day=1, month=1, year=21),
                    "id": 1,
                    "time": time(hour=11, minute=11),
                },
                {
                    "name": "name big",
                    "date": date(day=7, month=7, year=2001),
                    "id": 10,
                    "time": time(hour=22, minute=22),
                },
                {
                    "name": "name bigger",
                    "date": date(day=5, month=5, year=201),
                    "id": 100,
                    "time": time(hour=13, minute=13),
                },
            ],
            ["id", "time", "name", "date"],
            [
                "ID  | TIME  | NAME        | DATE      ",
                "----+-------+-------------+-----------",
                "1   | 11:11 | name        | 01/01/21  ",
                "10  | 22:22 | name big    | 07/07/2001",
                "100 | 13:13 | name bigger | 05/05/201 ",
            ],
        ),
        (
            [{"Id": 1, "date": "whatever", "tIme": time(hour=11, minute=11)}],
            ["Id", "tIme"],
            [
                "ID | TIME ",
                "---+------",
                "1  | 11:11",
            ],
        ),
    ],
)
def test_format_rows_given_valid_args(rows, cols, expected):
    for row, expected_row in zip(format_rows(rows, cols), expected):
        assert row == expected_row


@pytest.mark.parametrize(
    "rows,cols",
    [
        (
            [
                {"date": "some date"},
                {"date": "some date"},
                {"date": "some date"},
            ],
            ["date", "time"],
        ),
    ],
)
def test_format_rows_given_invalid_args(rows, cols):
    with pytest.raises(AssertionError):
        list(format_rows(rows, cols))


@pytest.mark.parametrize(
    "rows,column_widths,expected",
    [
        ({}, {}, {}),
        ({"a": "aa", "b": "bbb"}, {"a": 5, "b": 5}, {"a": "aa   ", "b": "bbb  "}),
        ({"a": "", "b": "bbb"}, {"a": 3, "b": 5}, {"a": "   ", "b": "bbb  "}),
    ],
)
def test_pad_row_values_given_valid_args(rows, column_widths, expected):
    assert pad_row_values(rows, column_widths) == expected


@pytest.mark.parametrize(
    "rows,column_widths",
    [
        ({"a": "aa", "b": "bbb", "c": "c"}, {"a": 3, "b": 5}),
        ({"a": "aa", "b": "bbb"}, {"a": 3, "b": 5, "c": 7}),
    ],
)
def test_pad_row_values_given_invalid_args(rows, column_widths):
    with pytest.raises(AssertionError):
        pad_row_values(rows, column_widths)
