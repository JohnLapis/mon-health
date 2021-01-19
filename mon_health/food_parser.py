import re
from datetime import datetime
from functools import reduce

from .db import Food
from .utils import parse_date, parse_time


class FoodParser:
    def __init__(self, _input):
        self.input = _input
        self.where_clause = None
        self.where_clause_filters = []
        self.sorting_clause = None
        self.limit_clause = None

    def match(self, pattern):
        return re.match(pattern, self.input, re.IGNORECASE)

    def parse(self):
        self.parse_where_clause()
        self.parse_sorting_clause()
        self.parse_limit_clause()

    def parse_where_clause(self):
        self.parse_name()
        self.parse_date()
        self.parse_time()
        if self.where_clause_filters:
            self.where_clause = reduce(lambda a, b: a & b, self.where_clause_filters)

    def parse_name(self):
        match = self.match(r"(.*?);\s*")
        if match:
            self.where_clause_filters.append(Food.name == match.groups()[0].strip())
            self.input = self.input[match.end() :]

    def parse_date(self):
        match = self.match(r"today *")
        if match:
            self.where_clause_filters.append(Food.date == datetime.now().date())
            self.input = self.input[match.end() :]
        else:
            match = self.match(r"(\d+$|\d+\s|\d+(/\d+)+)\s*")
            if match:
                self.where_clause_filters.append(
                    Food.date == parse_date(match.groups()[0])
                )
                self.input = self.input[match.end() :]

    def parse_time(self):
        match = self.match(r"(\d+:\d+) *")
        if match:
            self.where_clause_filters.append(
                Food.time == parse_time(match.groups()[0])
            )
            self.input = self.input[match.end() :]
        else:
            match = self.match(r"(\S+)h *")
            if match:
                hour = match.groups()[0]
                low = parse_time(hour + ":00")
                high = parse_time(hour + ":59")
                self.where_clause_filters.append(Food.time.between(low, high))
                self.input = self.input[match.end() :]

    def parse_sorting_clause(self):
        match = self.match(r"(?:order +by|sort) +(-?)(\w+)\b *")
        if match:
            field = getattr(Food, match.groups()[1])
            self.sorting_clause = field.desc() if match.groups()[0] else field
            self.input = self.input[match.end() :]

    def parse_limit_clause(self):
        match = self.match(r"limit +(\d+)\b *")
        if match:
            self.limit_clause = match.groups()[0]
            self.input = self.input[match.end() :]
