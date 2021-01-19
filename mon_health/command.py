import re
from datetime import datetime, time
from functools import reduce

DB = None
COMMAND_TABLE = {}


def parse_date(string):
    try:
        date_params = string.split("/")
        assert 1 <= len(date_params) <= 3
        year = datetime.now().year if len(date_params) < 3 else date_params[2]
        month = datetime.now().month if len(date_params) < 2 else date_params[1]
        day = date_params[0]
        return datetime(day=int(day), month=int(month), year=int(year))
    except (ValueError, AssertionError):
        raise InvalidDate


def parse_time(string):
    try:
        time_params = string.split(":")
        assert 1 <= len(time_params) <= 2
        minute = 0 if len(time_params) == 1 else time_params[1]
        hour = time_params[0]
        return time(hour=int(hour), minute=int(minute))
    except (ValueError, AssertionError):
        raise InvalidDate


def format_time(date):
    return date.strftime("%H:%M")


class InvalidTime(Exception):
    pass


class InvalidDate(Exception):
    pass


class AliasNotFound(Exception):
    pass


class CommandNotFound(Exception):
    pass


class Command:
    # def __init__(self, description):
    #     self.description = description
    #     self.db = DB

    description = "You should override this var."

    def exec(self, *args):
        # make it an abstract class? "import abc"
        raise Exception("You should override this method.")


class HelpCommand(Command):
    description = "Prints this help."

    @staticmethod
    def get_padding(text):
        offset = 20
        return (offset - len(text)) * " "

    @staticmethod
    def execute(args):
        if args == "":
            output = []
            for name, command in get_commands():
                output.append(
                    name + HelpCommand.get_padding(name) + command.description
                )
        else:
            command = get_command(args)
            output = [args + HelpCommand.get_padding(args) + command.description]

        return output


class InsertCommand(Command):
    description = "Inserts entry into database."


class FindCommand(Command):
    description = "Finds entry into database."

    @staticmethod
    def execute(args):
        def match_args(pattern):
            return re.match(pattern, args, re.IGNORECASE)

        try:
            q = Food.select()
            filters = []

            match = match_args(r"today *")
            if match:
                filters.append(Food.date == datetime.now().date())
                args = args[match.end() :]
            else:
                match = match_args(r"(\S+) *")
                if match and ":" not in match.group() and "h" not in match.group():
                    filters.append(Food.date == parse_date(match.groups()[0]))
                    args = args[match.end() :]

            match = match_args(r"(\d+:\d+) *")
            if match:
                filters.append(Food.time == parse_time(match.groups()[0]))
                args = args[match.end() :]
            else:
                match = match_args(r"(\S+)h *")
                if match:
                    hour = match.groups()[0]
                    low = parse_time(hour + ":00")
                    high = parse_time(hour + ":59")
                    filters.append(Food.time.between(low, high))
                    args = args[match.end() :]

            q = q.where(reduce(lambda a, b: a & b, filters))

            match = match_args(r"order +by +(\w+)\b *")
            if match:
                q = q.order_by(getattr(Food, match.groups()[0]))
                args = args[match.end() :]
            else:
                q = q.order_by(Food.date)
        except IndexError:
            raise "algo"

        match = match_args(r"limit +(\d+)\b *")
        if match:
            q = q.limit(match.groups()[0])

        output = []
        output.append("ID  TIME  NAME")
        for food in q:
            output.append(f"{food.id}  {format_time(food.time)}  {food.name}")

        return output


class UpdateCommand(Command):
    description = "Updates entry into database."


class DeleteCommand(Command):
    description = "Delete entry from database."

    @staticmethod
    def execute(args):
        output = []
        output.append("ID  TIME  NAME")
        for id in args.split(","):
            food = Food.get_by_id(id)
            output.append(f"{food.id}  {format_time(food.time)}  {food.name}")
            Food.delete_by_id(id)

        return output


class ExitCommand(Command):
    description = "Exits shell."

    @staticmethod
    def execute(*args):
        return []


def setup_commands(db, command_table=None, alias_table=None):
    global DB, Food, COMMAND_TABLE, ALIAS_TABLE

    DB = db
    Food = db.Food

    if command_table is None:
        COMMAND_TABLE = {
            "help": HelpCommand,
            "insert": InsertCommand,
            "find": FindCommand,
            "update": UpdateCommand,
            "delete": DeleteCommand,
            "exit": ExitCommand,
        }
    else:
        COMMAND_TABLE = command_table
    if alias_table is None:
        ALIAS_TABLE = {
            "h": "help",
            "i": "insert",
            "f": "find",
            "u": "update",
            "d": "delete",
            "today": "find today",
        }
    else:
        ALIAS_TABLE = alias_table


def parse_command(command):
    match = re.match(r"(?P<a>\w+) *(?P<args>.*)?", command)
    if match is None:
        raise SyntaxError
    return match.groups()


def run_command(input):
    try:
        name, args = parse_command(input)

        try:
            command = get_command(name)
        except CommandNotFound:
            input = get_alias(name)
            name, alias_args = parse_command(input)
            args = alias_args + args
            command = get_command(name)

        for output in command.execute(args):
            print(output)
    except CommandNotFound:
        print(f"Command '{name}' does not exist.")
    except AliasNotFound:
        print(f"Alias '{name}' does not exist.")
    except SyntaxError:
        print("A command should be composed of lower-case letters.")


def get_alias(name):
    try:
        return ALIAS_TABLE[name]
    except KeyError:
        raise AliasNotFound


def get_command(name):
    try:
        return COMMAND_TABLE[name]
    except KeyError:
        raise CommandNotFound


def get_commands():
    return COMMAND_TABLE.items()


def get_aliases():
    return ALIAS_TABLE.items()
