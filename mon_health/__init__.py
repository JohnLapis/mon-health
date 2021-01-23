from . import db
from .command import run_command, setup_commands


def setup():
    setup_commands(db)
