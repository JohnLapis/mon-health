from . import db
from .command import execute_query, setup_commands


def setup():
    setup_commands(db)
