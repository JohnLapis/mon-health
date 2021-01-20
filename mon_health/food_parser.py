import re
from datetime import datetime

from .db import Food
from .utils import InvalidTime, convert_to_date, convert_to_time


class KeywordNotFound(Exception):
    pass


class InvalidExpression(Exception):
    pass


class InvalidValue(Exception):
    pass


class InvalidName(Exception):
    pass


class InvalidSortField(Exception):
    pass


class InvalidLimit(Exception):
    pass


class FoodParser:
    exprs = [
        {
            "name": "name",
            "keyword_pattern": r"name|n",
            "value_pattern": r"[`'\"].*?[`'\"]",
        },
        {
            "name": "date",
            "keyword_pattern": r"date|d",
            "value_pattern": r"\d{1,2}(/\d{1,2}(/\d{1,4})?)?",
        },
        {
            "name": "time",
            "keyword_pattern": r"time|t",
            "value_pattern": r"\d{1,2}:\d{2}|\d{1,2}h+",
        },
        {
            "name": "sort",
            "keyword_pattern": r"sort|s",
            "value_pattern": r"-?\w+(,-?\w+)*",
        },
        {
            "name": "limit",
            "keyword_pattern": r"limit|l",
            "value_pattern": r"\d+",
        },
    ]
    keyword_patterns = "|".join([e["keyword_pattern"] for e in exprs])

    def __init__(self, _input):
        self.input = _input
        self.where_clause = None
        self.sort_clause = None
        self.limit_clause = None

    def parse_expr(self, *, name, keyword_pattern, value_pattern):
        keyword, keyword_start, keyword_end = self.search_keyword(
            keyword_pattern, self.input
        )
        value, _, value_end = self.match_value(
            value_pattern, self.input[keyword_end:]
        )
        expr_start, expr_end = keyword_start, keyword_end + value_end
        # whitespace is added in between since it's always matched
        self.input = (self.input[:expr_start] + " " + self.input[expr_end:]).strip()
        self.get_parser(name)(value)

    def parse(self):
        for expr in self.exprs:
            try:
                self.parse_expr(**expr)
            except KeywordNotFound:
                pass

        if self.input:
            raise InvalidExpression(
                f"Expression '{self.input}' could not be parsed."
            )

    def ends_with_keyword(self, string):
        return re.search(f"({self.keyword_patterns})$", string, re.I)

    def search_keyword(self, pattern, string):
        try:
            pattern = r"(\s+|^)(" + pattern + r")(\s+|$)"
            match = re.search(pattern, string, re.I)
            assert match and not self.ends_with_keyword(string[: match.start()])
            return (match.group(2), match.start(), match.end())
        except AssertionError:
            raise KeywordNotFound(f"String doesn't match pattern '{pattern}'.")

    def match_value(self, pattern, string):
        try:
            pattern = r"(\s+|^)(" + pattern + r")(\s+|$)"
            match = re.match(pattern, string, re.I)
            assert match
            return (match.group(2), match.start(), match.end())
        except AssertionError:
            invalid_value = re.match(r"\S*", string).group()
            raise InvalidValue(f"Value '{invalid_value}' is invalid.")

    def get_parser(self, name):
        return getattr(self, f"parse_{name}")

    def add_to_where_clause(self, value):
        if self.where_clause is None:
            self.where_clause = value
        else:
            self.where_clause &= value

    def parse_name(self, string):
        if not re.match(r"([\"'`]).*\1", string):
            raise InvalidName("Name should be quoted.")
        if not string[1:-1]:
            raise InvalidName("Name can't be empty.")

        self.add_to_where_clause(Food.name == string[1:-1])

    def parse_date(self, value):
        if re.match(value, "today", re.I):
            self.add_to_where_clause(Food.date == datetime.now().date())
        else:
            self.add_to_where_clause(Food.date == convert_to_date(value))

    def parse_time(self, value):
        if value.endswith("h"):
            hour = value[:-1]
            low = convert_to_time(hour + ":00")
            high = convert_to_time(hour + ":59")
            self.add_to_where_clause(Food.time.between(low, high))
        elif ":" in value:
            self.add_to_where_clause(Food.time == convert_to_time(value))
        else:
            raise InvalidTime

    def add_to_sort_clause(self, value):
        if self.sort_clause is None:
            self.sort_clause = []
        self.sort_clause.append(value)

    def parse_sort(self, value):
        try:
            for param in re.split(r"\s*,\s*", value):
                if param.startswith("-"):
                    field = getattr(Food, param[1:]).desc()
                else:
                    field = getattr(Food, param).asc()
                self.add_to_sort_clause(field)
        except AttributeError:
            raise InvalidSortField

    def parse_limit(self, value):
        try:
            limit = int(value)
            assert limit >= 0
            self.limit_clause = limit
        except (ValueError, TypeError, AssertionError):
            raise InvalidLimit("Limit should be a positive integer.")
