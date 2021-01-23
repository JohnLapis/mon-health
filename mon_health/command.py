import re

from peewee import IntegrityError

from .food_parser import FoodParser
from .utils import InvalidCommand, format_rows, parse_command


class AliasNotFound(Exception):
    pass


class CommandNotFound(Exception):
    pass


class NameFieldNotFound(Exception):
    pass


class IdFieldNotFound(Exception):
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
        return [
            {"name": name} for name in sorted(re.split(r"\s*,\s*", args.strip()))
        ]

    @staticmethod
    def execute(args):
        try:
            Food.insert_many(InsertCommand.parse_args(args)).execute()
            return []
        except Exception as e:
            return [e.args[0]]


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
            return [e.args[0]]


class UpdateCommand(Command):
    description = "Updates entry into database."

    @staticmethod
    def parse_args(args):
        parser = FoodParser(args)
        parser.parse()
        params = {}

        if not parser.id:
            raise IdFieldNotFound
        params["id"] = parser.id
        if not parser.name:
            raise NameFieldNotFound
        params["name"] = parser.name
        if parser.date:
            params["date"] = parser.date
        if parser.time:
            params["time"] = parser.time

        return params

    @staticmethod
    def execute(args):
        try:
            params = UpdateCommand.parse_args(args)
        except IdFieldNotFound:
            return ["Id field should be given."]
        except NameFieldNotFound:
            return ["Name field should be given."]
        except Exception as e:
            return [e.args[0]]

        try:
            rows_modified = Food.replace(**params).execute()
        except IntegrityError:
            return ["Invalid update query."]
        except Exception as e:
            return [e.args[0]]

        if rows_modified == 1:
            return [f"{rows_modified} row modified."]
        return [f"{rows_modified} rows modified."]


class DeleteCommand(Command):
    description = "Delete entry from database."

    @staticmethod
    def parse_args(args):
        parser = FoodParser(args)
        parser.parse()
        return Food.delete().where(parser.where_clause)

    @staticmethod
    def execute(args):
        try:
            query = DeleteCommand.parse_args(args)
        except IdFieldNotFound:
            return ["Id field should be given."]
        except Exception as e:
            return [e.args[0]]

        try:
            rows_modified = query.execute()
        except IntegrityError:
            return ["Invalid delete query."]
        except Exception as e:
            return [e.args[0]]

        if rows_modified == 1:
            return [f"{rows_modified} row modified."]
        return [f"{rows_modified} rows modified."]


class ExitCommand(Command):
    description = "Exits shell."

    @staticmethod
    def execute(args):
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
            "today": "find date today",
            "last": "find date today limit",
            "id": "find id",
            "name": "find name",
            "date": "find date",
            "time": "find time",
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
