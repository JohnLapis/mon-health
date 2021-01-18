#!/usr/bin/python3

import click

from mon_health import *


@click.command()
def main():
    print("mon-health 0.0.1. Type 'help' for help.")
    setup()
    while True:
        command = input(">>> ").strip()
        if command:
            run_command(command)

    # teardown()


if __name__ == "__main__":
    main()
