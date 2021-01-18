from peewee import *
from datetime import datetime

db = SqliteDatabase('health.db')

def current_time():
    return datetime.now().time()


def current_date():
    return datetime.now().date()


class BaseModel(Model):
    class Meta:
        database = db


class Food(BaseModel):
    name = TextField()
    time = TimeField(default=current_time)
    date = DateField(default=current_date)


def get_db():
    return db.connect('health.db')

def init_db():
    db.create_tables([Food])
