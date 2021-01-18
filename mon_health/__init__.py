import re

from . import db
from .command import CommandNotFound, get_command, setup_commands


def setup():
    # db = db.get_db()
    # setup_commands(db)
    setup_commands(["oi"])


def teardown():
    db.close()


def parse_command(command):
    return re.match(r"(?P<a>\w+) *(?P<args>.*)?", command).groups()


def run_command(command):
    # args should come parsed already
    name, args = parse_command(command)
    try:
        for output in get_command(name).execute(args):
            print(output)
    except CommandNotFound:
        print(f"Command '{name}' does not exist.")
