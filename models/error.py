import datetime as dt
import uuid

import peewee as pw
from database import BaseModel, JSONField, db
from library.types import error_log_types


class Error(BaseModel):
    """
    A model that stores information about an error. This is usually created
    through `utils.log_error`.
    """

    id = pw.UUIDField(primary_key=True, unique=True, default=uuid.uuid4)
    created_at = pw.DateTimeField(default=dt.datetime.now)

    type = pw.TextField(choices=error_log_types)
    title = pw.TextField()
    message = pw.TextField()
    traceback = pw.TextField(null=True)
    metadata = JSONField(null=True)


db.create_tables([Error])
