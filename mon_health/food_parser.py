import re
from functools import reduce
from datetime import datetime

from .db import Food
from .utils import convert_to_date, convert_to_time


class KeywordNotFound(Exception):
    pass


class InvalidExpression(Exception):
    pass


class InvalidValue(Exception):
    pass


class InvalidName(Exception):
    pass


class InvalidColumn(Exception):
    pass


class InvalidLimit(Exception):
    pass


class Match:
    def __init__(self, matched, start, end):
        self.matched = matched
        self.start = start
        self.end = end


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
            "value_pattern": r"\d{1,2}(/\d{1,2}(/\d{1,4})?)?|today",
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
        {
            "name": "returning",
            "keyword_pattern": r"returning|\|",
            "value_pattern": r"\w+(,\w+)*",
        },
    ]
    keyword_patterns = "|".join([e["keyword_pattern"] for e in exprs])

    def __init__(self, _input):
        self.input = _input
        self.where_clause_exprs = []
        self.sort_clause = []
        self.limit_clause = -1
        self.returning_clause = []

    def parse_expr(self, *, name, keyword_pattern, value_pattern):
        keyword_match = self.search_keyword(keyword_pattern, self.input)
        value_match = self.match_value(
            value_pattern, self.input[keyword_match.end :]
        )
        expr_start = keyword_match.start
        expr_end = keyword_match.end + value_match.end
        # whitespace is added in between since it's always matched
        self.input = (self.input[:expr_start] + " " + self.input[expr_end:]).strip()
        self.get_parser(name)(value_match.matched)

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
            return Match(match.group(2), match.start(), match.end())
        except AssertionError:
            raise KeywordNotFound(f"String doesn't match pattern '{pattern}'.")

    def match_value(self, pattern, string):
        try:
            pattern = r"(\s+|^)(" + pattern + r")(\s+|$)"
            match = re.match(pattern, string, re.I)
            assert match
            return Match(match.group(2), match.start(), match.end())
        except AssertionError:
            invalid_value = re.match(r"\S*", string).group()
            raise InvalidValue(f"Value '{invalid_value}' is invalid.")

    def get_parser(self, name):
        return getattr(self, f"parse_{name}")

    @property
    def where_clause(self):
        if self.where_clause_exprs:
            return reduce(lambda a, b: a & b, self.where_clause_exprs)
        else:
            return True

    def parse_name(self, string):
        if not re.match(r"([\"'`]).*\1", string):
            raise InvalidName("Name should be quoted.")
        if not string[1:-1]:
            raise InvalidName("Name can't be empty.")

        self.where_clause_exprs.append(Food.name == string[1:-1])

    def parse_date(self, string):
        if re.match(string, "today", re.I):
            expr = Food.date == datetime.now().date()
        else:
            expr = Food.date == convert_to_date(string)

        self.where_clause_exprs.append(expr)

    def parse_time(self, string):
        if string.endswith("h"):
            hour = string[:-1]
            low = convert_to_time(hour + ":00")
            high = convert_to_time(hour + ":59")
            expr = Food.time.between(low, high)
        else:
            expr = Food.time == convert_to_time(string)

        self.where_clause_exprs.append(expr)

    def parse_sort(self, string):
        try:
            columns = []
            for name in string.split(","):
                if name.startswith("-"):
                    columns.append(getattr(Food, name[1:]).desc())
                else:
                    columns.append(getattr(Food, name).asc())
            self.sort_clause = columns
        except AttributeError:
            raise InvalidColumn

    def parse_limit(self, string):
        try:
            limit = int(string)
            assert limit >= 0
            self.limit_clause = limit
        except (ValueError, TypeError, AssertionError):
            raise InvalidLimit("Limit should be a positive integer.")

    def parse_returning(self, string):
        if re.match(string, "all", re.I):
            self.returning_clause = []
            return

        try:
            self.returning_clause = [
                getattr(Food, name) for name in string.split(",")
            ]
        except AttributeError:
            raise InvalidColumn
