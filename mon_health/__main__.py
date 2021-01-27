import click

from mon_health import db
from mon_health.command import execute_query, setup_commands


def setup():
    setup_commands(db)


@click.command()
def main():
    print("mon-health 1.0.0-alpha. Type 'help' for help.")
    setup()
    while True:
        try:
            queries = [query.strip() for query in input(">>> ").split(";")]
            for query in queries:
                if query:
                    execute_query(query)
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            execute_query("exit")
            break


if __name__ == "__main__":
    main()
