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


def parse_query(command):
    match = re.match(r"\s*(?P<name>\S+)(\s+(?P<args>.*))?", command)
    if match is None:
        raise InvalidCommand("Invalid command.")
    return match.groupdict()["name"], match.groupdict("")["args"].strip()


def format_time(value):
    assert isinstance(value, time)
    return value.strftime("%H:%M")


def format_date(value):
    assert isinstance(value, datetime)
    return value.strftime("%d/%m/%Y")


formatters = {
    time: format_time,
    datetime: format_date,
    str: str,
    int: str,
}


def format_value(value):
    return formatters[type(value)](value)


def format_column_name(name):
    return name.upper()


def pad_row_values(row, column_widths):
    assert set(row.keys()) == set(column_widths.keys())
    return {col: row[col].ljust(width) for col, width in column_widths.items()}


def format_rows(rows, cols, col_sep="|"):
    assert len(col_sep) == 1
    col_sep = " " + col_sep + " "

    column_names_row = {col: format_column_name(col) for col in cols}
    max_column_lengths = {col: len(column_names_row[col]) for col in cols}

    formatted_rows = []
    for row in rows:
        assert set(cols).issubset(set(row.keys()))
        formatted_row = {}
        for col in cols:
            formatted_row[col] = format_value(row[col])
            max_column_lengths[col] = max(
                max_column_lengths[col], len(formatted_row[col])
            )

        formatted_rows.append(formatted_row)

    yield col_sep.join(pad_row_values(column_names_row, max_column_lengths).values())
    yield "-+-".join(["-" * length for length in max_column_lengths.values()])

    for row in formatted_rows:
        yield col_sep.join(pad_row_values(row, max_column_lengths).values())
