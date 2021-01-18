class Command:
    def __init__(self, description):
        self.description = description
        self.conn = conn
        # how many threads?
        self a = self.conn.cursor()

    def exec(self, *args):
        # make it an abstract class? "import abc"
        raise Exception("You should override this method.")


class HelpCommand(Command):
    def __init__(self):
        super("Prints this help.")

    def get_padding(text):
        offset = 20
        return offset - len(text) * " "

    def exec(self, *args):
        for command in COMMMAND_TABLE.items():
            print(command.name + get_padding() + commmand.description)


class InsertCommand(Command):
    def __init__(self):
        super("Inserts entry into database.")

class FindCommand(Command):
    def __init__(self):
        super("Finds entry into database.")

class UpdateCommand(Command):
    def __init__(self):
        super("Updates entry into database.")

class DeleteCommand(Command):
    def __init__(self):
        super("Delete entry from database.")

class ExitCommand(Command):
    def __init__(self):
        super("Exits shell.")


def setup_commands(db):
    global conn
    conn = db

    COMMAND_TABLE = {
        "help": HelpCommand(),
        "insert": InsertCommand(),
        "find": FindCommand(),
        "update": UpdateCommand(),
        "delete": DeleteCommand(),
        "exit": ExitCommand(),
    }
