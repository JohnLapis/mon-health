#!/usr/bin/python3

import click
import .db
from .command import setup_commands


def setup():
    # db = db.get_db()
    # setup_commands(db)
    setup_commands(["oi"])

def teardown():
    db.close()


def run_command(name):
    COMMAND_TABLE[name].exec()


@click.command()
def main():
    print("mon-health 0.0.1. Type 'help' for help.")
    setup()
    while True:
        command = input(">>> ")
        run_command(command)

    # teardown()


if __name__ == "__main__":
    main()
