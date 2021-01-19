#!/usr/bin/env python3

import click

from mon_health import setup, run_command


@click.command()
def main():
    print("mon-health 0.0.1. Type 'help' for help.")
    setup()
    while True:
        try:
            command = input(">>> ").strip()
            if command:
                run_command(command)
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            run_command("exit")
            break


if __name__ == "__main__":
    main()
