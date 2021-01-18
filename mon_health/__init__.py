import re

from . import db
from .command import CommandNotFound, get_command, setup_commands


def setup():
    setup_commands(db)


def parse_command(command):
    match = re.match(r"(?P<a>\w+) *(?P<args>.*)?", command)
    if match is None:
        raise SyntaxError
    return match.groups()


def run_command(command):
    try:
        # args should come parsed already
        name, args = parse_command(command)
        for output in get_command(name).execute(args):
            print(output)
    except CommandNotFound:
        print(f"Command '{name}' does not exist.")
    except SyntaxError:
        print(f"A command should be composed of lower-case letters.")
