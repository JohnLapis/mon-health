import re
from datetime import datetime, time
from functools import reduce

DB = None
COMMAND_TABLE = {}

from .utils import InvalidCommand, format_time, parse_command, parse_date, parse_time





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

    @staticmethod
    def execute(args):
        Food.insert_many(
            [{"name": name.strip()} for name in args.split(",")]
        ).execute()

        return []


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

            match = match_args(r"(?:order +by|sort) +(-?)(\w+)\b *")
            if match:
                field = getattr(Food, match.groups()[1])
                q = q.order_by(field.desc() if match.groups()[0] else field)
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

    @staticmethod
    def execute(args):
        id, name = args.split(",")
        Food.replace(id=id.strip(), name=name.strip()).execute()

        return []


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
            "last": "find today limit",
        }
    else:
        ALIAS_TABLE = alias_table


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
    except CommandNotFound:
        print(f"Command '{name}' does not exist.")
    except AliasNotFound:
        print(f"Alias '{name}' does not exist.")
    except InvalidCommand:
        print("A command should be composed of lower-case letters.")

    for output in command.execute(args):
        print(output)


def get_command(name):
    try:
        return COMMAND_TABLE[name]
    except KeyError:
        raise CommandNotFound


def get_commands():
    return COMMAND_TABLE.items()


def get_alias(name):
    try:
        return ALIAS_TABLE[name]
    except KeyError:
        raise AliasNotFound


def get_aliases():
    return ALIAS_TABLE.items()
