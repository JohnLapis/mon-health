from datetime import datetime, time

from peewee import CharField, DateField, Model, SqliteDatabase, TimeField

db = SqliteDatabase("health.db")


def current_time():
    now = datetime.now().time()
    return time(hour=now.hour, minute=now.minute)


def current_date():
    return datetime.now().date()


class BaseModel(Model):
    class Meta:
        database = db


class Food(BaseModel):
    name = CharField(max_length=20)
    time = TimeField(default=current_time)
    date = DateField(default=current_date)


def init_db():
    db.create_tables([Food])
