"""
This module contains metric related models. Metrics are used to determine how
Windows Image Explorer is performing. Metrics will be reported to WIE's servers
by default but it can be disabled in the config file.
"""

import uuid

import peewee as pw
from database import BaseModel, db
from library.types import time_metric_types


class TimeMetric(BaseModel):

    """
    Logs time related performance. Useful for things like timing functions, operations, etc.
    """

    id = pw.UUIDField(default=uuid.uuid4, primary_key=True)
    type = pw.TextField(choices=time_metric_types)

    tt = pw.FloatField()
    title = pw.TextField(null=True)
    message = pw.TextField(null=True)


db.create_tables([TimeMetric])
