from . import db
from .command import setup_commands, run_command


def setup():
    setup_commands(db)
