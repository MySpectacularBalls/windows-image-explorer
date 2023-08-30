import datetime as dt
import uuid

import peewee as pw
from database import BaseModel, db

from .object import Object


class Query(BaseModel):
    """
    A user's query. Used for the search history as well as caching.
    """

    id = pw.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = pw.DateTimeField(default=dt.datetime.now)

    # Parameters
    query = pw.TextField()
    n_results = pw.IntegerField()
    max_distance = pw.FloatField()

    returned_results = pw.IntegerField()

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "query": self.query,
            "n_results": self.n_results,
            "max_distance": self.max_distance,
            "returned_results": self.returned_results,
        }


class QueryResult(BaseModel):
    query = pw.ForeignKeyField(Query, backref="results")
    object = pw.ForeignKeyField(Object)
    distance = pw.FloatField()

    def to_json(self) -> dict:
        return {"object": self.object, "distance": self.distance}


db.create_tables([Query, QueryResult])
