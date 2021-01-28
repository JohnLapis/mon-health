import click, curses, time

from mon_health.command import execute_query, setup_commands
from mon_health.db import tables


def setup():
    setup_commands(tables)


def execute(input):
    queries = [query.strip() for query in input.split(";")]
    # for query in queries:
    #     if query:
    #         return execute_query(query)
    # return "\n".join([execute_query(query) for query in queries if query])
    return "\n".join([execute_query(query) for query in queries if query])

def read_char(input, screen):
    if c == KEY_ENTER:
        screen.addstr("\n")
        screen.addstr(execute(input))
        screen.addstr("\n>>> ")
        input = ""
    else:
        # screen.addstr(str(c == "\x1b0x62"))
        # screen.addstr(str(hex(c)))
        screen.addstr(c)

    return input

def read_char_in_escape_sequence(input, screen):
    escape_sequence = ""
    in_escape_sequence = True

    if input.endswith(KEY_CTRL_D):
        screen.addstr(execute("exit"))
        break
    elif input.endswith(KEY_LEFT_ARROW):
        screen.addstr("left arrow")
        # y, x = curses.getyx()
        # curses.setyx(y, x - 1)
        escape_sequence = KEY_LEFT_ARROW
    elif input.endswith(KEY_ALT_F):
        screen.addstr("alt f")
    elif input.endswith(KEY_ALT_B):
    screen.addstr("alt b")

    if escape_sequence:
        in_escape_sequence = False
        input = input[:-len(escape_sequence)]

    return input, in_escape_sequence

# enum
KEY_CTRL_A = "\x01"
KEY_CTRL_B = "\x02"
KEY_CTRL_C = "\x03"
KEY_CTRL_D = "\x04"
KEY_CTRL_E = "\x05"
KEY_CTRL_F = "\x06"
KEY_CTRL_K = "\x0b"
KEY_CTRL_N = "\x0e"
KEY_CTRL_P = "\x10"
KEY_CTRL_U = "\x15"
KEY_ALT_B = "\x1b\x62"
KEY_ALT_F = "\x1b\x66"

KEY_ENTER = "\n"
KEY_BACKSPACE = "\x7f"
KEY_LEFT_ARROW = "\x1b\x5b\x44"

ESCAPE_SEQUENCES = [KEY_ALT_B, KEY_ALT_F, KEY_LEFT_ARROW]
history = []
def main(screen):
    input = ""
    screen.addstr("mon-health 1.0.0-alpha. Type 'help' for help.\n")
    setup()
    # global C
    # C = screen.getkey()
    screen.addstr(">>> ")
    in_escape_sequence = False
    while True:
        try:
            c = screen.getkey()
            # c = screen.getch()
            input += c
            if  c.isalnum() and not in_escape_sequence:
                input = read_char(input, screen)
            else:
                input, in_escape_sequence = read_char_in_escape_sequence(input, screen)

        except KeyboardInterrupt:
            screen.addstr("\n>>> ")


if __name__ == "__main__":
    screen = curses.initscr()
    curses.noecho()
    curses.cbreak()
    main(screen)
    curses.nocbreak()
    curses.echo()
    curses.endwin()
