import re
from datetime import datetime, time


class InvalidTime(Exception):
    pass


class InvalidDate(Exception):
    pass


class InvalidCommand(Exception):
    pass


def convert_to_date(string):
    try:
        date_params = string.split("/")
        assert 1 <= len(date_params) <= 3
        year = datetime.now().year if len(date_params) < 3 else date_params[2]
        month = datetime.now().month if len(date_params) < 2 else date_params[1]
        day = date_params[0]
        return datetime(day=int(day), month=int(month), year=int(year))
    except (ValueError, AssertionError):
        raise InvalidDate


def convert_to_time(string):
    try:
        time_params = string.split(":")
        assert 1 <= len(time_params) <= 2
        minute = 0 if len(time_params) == 1 else time_params[1]
        hour = time_params[0]
        return time(hour=int(hour), minute=int(minute))
    except (ValueError, AssertionError):
        raise InvalidTime


def format_time(time):
    return time.strftime("%H:%M")


def parse_command(command):
    match = re.match(r"\s*(?P<a>\S+)\s*(?P<args>.*)?", command)
    if match is None:
        raise InvalidCommand
    name, args = match.groups()
    return [name, "" if args is None else args.strip()]
