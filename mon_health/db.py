from datetime import datetime

from peewee import DateField, Model, SqliteDatabase, CharField, TimeField

db = SqliteDatabase("health.db")


def current_time():
    return datetime.now().time()


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
