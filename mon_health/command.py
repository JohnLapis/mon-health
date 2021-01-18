from datetime import datetime

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


class InvalidDate(Exception):
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


class UpdateCommand(Command):
    description = "Updates entry into database."


class DeleteCommand(Command):
    description = "Delete entry from database."


class ExitCommand(Command):
    description = "Exits shell."

    @staticmethod
    def execute(*args):
        return []


def setup_commands(db, command_table=None):
    global DB, Food, COMMAND_TABLE

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


def get_command(name):
    try:
        return COMMAND_TABLE[name]
    except KeyError:
        raise CommandNotFound


def get_commands():
    return COMMAND_TABLE.items()
