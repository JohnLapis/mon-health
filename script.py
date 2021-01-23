#!/usr/bin/env python3

import click

from mon_health import execute_query, setup


@click.command()
def main():
    print("mon-health 0.0.1. Type 'help' for help.")
    setup()
    while True:
        try:
            queries = [query.strip() for query in input(">>> ").split(";")]
            for query in queries:
                if query:
                    execute_query(query)
                    print()
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            execute_query("exit")
            break


if __name__ == "__main__":
    main()
