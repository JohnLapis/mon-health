import re

from .food_parser import FoodParser
from .utils import (
    format_time,
    parse_command,
    convert_to_date,
    convert_to_time,
    InvalidCommand,
    InvalidDate,
    InvalidTime,
)


class AliasNotFound(Exception):
    pass


class CommandNotFound(Exception):
    pass


class InvalidArgs(Exception):
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
    def parse_args(args):
        return sorted(re.split(r"\s*,\s*", args.strip()))

    @staticmethod
    def execute(args):
        Food.insert_many(
            [{"name": name} for name in InsertCommand.parse_args(args)]
        ).execute()

        return []


class FindCommand(Command):
    description = "Finds entry into database."

    @staticmethod
    def parse_args(args):
        parser = FoodParser(args)
        parser.parse()
        return (
            Food.select(*parser.returning_clause)
            .where(parser.where_clause)
            .order_by(*(parser.sort_clause or (Food.date.asc(), Food.time.asc())))
            .limit(parser.limit_clause)
            .dicts()
        )

    @staticmethod
    def execute(args):
        try:
            query = FindCommand.parse_args(args)
            return format_rows(query)
        except Exception as e:
            return [e.msg]


class UpdateCommand(Command):
    description = "Updates entry into database."

    @staticmethod
    def parse_args(args):
        def add_to_parsed_args(key, value):
            if key in parsed_args:
                raise InvalidArgs
            else:
                parsed_args[key] = value

        try:
            split_args = [arg.strip() for arg in args.split(",")]
            parsed_args = {"id": split_args.pop(0)}
            assert split_args
            for arg in split_args:
                if "/" in arg:
                    add_to_parsed_args("date", parse_date(arg))
                elif ":" in arg:
                    add_to_parsed_args("time", parse_time(arg))
                else:
                    add_to_parsed_args("name", arg)

            return parsed_args
        except (AssertionError, IndexError, InvalidDate, InvalidTime):
            raise InvalidArgs

    @staticmethod
    def execute(args):
        try:
            # print(args)
            # Food.replace(id=args, time=parse_time("16:16")).execute()

            params = UpdateCommand.parse_args(args)
            Food.replace(**params).execute()
            return []
        except IntegrityError:
            return ["Name field should be given."]
            # raise e


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
        print("Invalid command.")

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
