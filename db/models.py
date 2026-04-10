import sys
from peewee import Model, UUIDField, TextField, CharField, DateTimeField, ForeignKeyField, FloatField
from playhouse.sqlite_ext import SqliteExtDatabase
from config import config

db = SqliteExtDatabase(config.DB_PATH)

class BaseModel(Model):
    class Meta:
        database = db

class Job(BaseModel):
    id = UUIDField(primary_key=True)
    topic = TextField()
    approved_topic = TextField(null=True)   # Operator-approved topic title from Gate 1
    status = CharField()                    # "running"|"paused_<AgentName>"|"completed"|"abandoned"|"failed"
    revenue_inr = FloatField(null=True)     # Populated by FeedbackAgent
    created_at = DateTimeField()
    updated_at = DateTimeField()

class AgentRun(BaseModel):
    id = UUIDField(primary_key=True)
    job = ForeignKeyField(Job, backref='agent_runs')
    agent_name = CharField()
    input_payload = TextField()   # JSON string
    output_payload = TextField()  # JSON string
    status = CharField()
    started_at = DateTimeField()
    finished_at = DateTimeField()
    error = TextField(null=True)

def init_db():
    db.connect()
    db.create_tables([Job, AgentRun])
    print(f"Database initialised at {config.DB_PATH}")

if __name__ == "__main__":
    init_db()
