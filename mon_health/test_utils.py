from datetime import datetime, time

import pytest

from .utils import (
    InvalidCommand,
    InvalidDate,
    InvalidTime,
    parse_command,
    parse_date,
    parse_time,
)


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


@pytest.mark.parametrize(
    "string,expected",
    [
        ("1", time(hour=1, minute=0)),
        ("01", time(hour=1, minute=0)),
        ("12:1", time(hour=12, minute=1)),
        ("1:01", time(hour=1, minute=1)),
    ],
)
def test_parse_time_given_valid_input(string, expected):
    assert parse_time(string) == expected


@pytest.mark.parametrize("string", ["", "a", "1:a", "1:1:1"])
def test_parse_time_given_invalid_input(string):
    with pytest.raises(InvalidTime):
        parse_time(string)


@pytest.mark.parametrize(
    "string,expected",
    [
        ("a", ["a", ""]),
        ("a b", ["a", "b"]),
        ("   a    $   ", ["a", "$"]),
        ("a 2       b", ["a", "2       b"]),
    ],
)
def test_parse_command_given_valid_input(string, expected):
    assert parse_command(string) == expected


@pytest.mark.parametrize("string", ["", " "])
def test_parse_command_given_invalid_input(string):
    with pytest.raises(InvalidCommand):
        parse_command(string)
