import os
from datetime import datetime, time
from pathlib import Path

from peewee import CharField, DateField, Model, SqliteDatabase, TimeField


def get_app_dir():
    try:
        XDG_DATA_HOME = os.getenv("XDG_DATA_HOME")

        if XDG_DATA_HOME:
            DATA_DIR = Path(XDG_DATA_HOME)
        else:
            DATA_DIR = Path(os.getenv("HOME")) / ".local" / "share"

        return DATA_DIR / "mon-health"
    except TypeError:
        raise Exception("'HOME' environment variable is not set.")


APP_DIR = get_app_dir()
if not APP_DIR.exists():
    os.mkdir(APP_DIR)

DB = SqliteDatabase(str(APP_DIR / "health.db"))


def current_time():
    now = datetime.now().time()
    return time(hour=now.hour, minute=now.minute)


def current_date():
    return datetime.now().date()


class BaseModel(Model):
    class Meta:
        database = DB


class Food(BaseModel):
    name = CharField(max_length=20)
    time = TimeField(default=current_time)
    date = DateField(default=current_date)


tables = {table.__name__.lower(): table for table in [Food]}
if not set(DB.get_tables()).issuperset(tables.keys()):
    DB.create_tables(tables.values())
