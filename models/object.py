import datetime as dt
import os
import uuid
from typing import Optional

from database import BaseModel, JSONField, db
from library import utils
from library.types import definition_types, ignored_file_types, object_types
from peewee import (
    BooleanField,
    DateTimeField,
    FloatField,
    ForeignKeyField,
    TextField,
    UUIDField,
)


class IgnoredFile(BaseModel):
    """
    Used for files that should be ignored when scanning. The `type` attribute is the
    reason as to why the file should be ignored.
    """

    file_id = TextField(index=True, primary_key=True)
    type = TextField(choices=ignored_file_types, null=True)


class Object(BaseModel):

    """
    A object is a file that can be queried with windows image explorer.
    """

    id = UUIDField(primary_key=True, unique=True, default=uuid.uuid4)
    created_at = DateTimeField(default=dt.datetime.now)
    type = TextField(choices=object_types)

    path = TextField()
    name = TextField()
    file_id = TextField(index=True, unique=True)
    file_creation_date = DateTimeField()
    metadata = JSONField(null=True)

    processed = BooleanField(default=False)
    generated_embeddings = BooleanField(default=False)
    last_processed_time = DateTimeField(null=True)

    error = BooleanField(default=False)
    error_traceback = TextField(null=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"

    def to_json(self) -> dict:
        return {
            "id": str(self.id),
            "created_at": self.created_at,
            "type": self.type,
            "path": self.path,
            "name": self.name,
            "file_id": self.file_id,
            "file_creation_date": self.file_creation_date,
            "metadata": self.metadata,
            "processed": self.processed,
            "last_processed_time": self.last_processed_time,
            "error": self.error,
            "error_traceback": self.error_traceback,
            "generated_embeddings": self.generated_embeddings,
        }

    @classmethod
    def from_path(cls, path: str) -> Optional["Object"]:
        """
        Create a object from a file path.

        Parameters
        ----------
        `path` : str
            The path to the file.

        Returns
        -------
        `Optional[Object]` :
            The created object. None if the provided file path can't be a valid object.
        """

        metadata: dict = {"file_size": os.path.getsize(path)}
        type = utils.get_object_type_from_file(path)
        if type == "image":
            resolution = utils.get_image_resolution(path)
            if resolution is None:
                utils.log_error(
                    type="resolution-not-found",
                    title="Resolution not found",
                    message=f"Not saving '{path}' as an image object.",
                    metadata={"path": path},
                )
                return

            metadata["resolution"] = {
                "width": resolution[0],
                "height": resolution[1],
                "total": resolution[0] + resolution[1],
            }

        return cls.create(
            type=type,
            path=path,
            name=os.path.basename(path),
            file_id=utils.get_file_id(path),
            file_creation_date=dt.datetime.fromtimestamp(os.path.getctime(path)),
            metadata=metadata,
        )


class ObjectDefinition(BaseModel):
    """
    A object definition contains processed information about a file. Information such as
    image-to-text descriptions, embeddings, etc.
    """

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = DateTimeField(default=dt.datetime.now)
    type = TextField(choices=definition_types)

    content = TextField()
    tt = FloatField()
    model = TextField(null=True)

    object = ForeignKeyField(Object, backref="definitions")

    def __str__(self) -> str:
        content = (
            (self.content[:75] + "...") if len(str(self.content)) > 75 else self.content
        )

        return f"{content} ({self.id}, {self.type})"

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "type": self.type,
            "content": self.content,
            "tt": self.tt,
            "model": self.model,
        }


db.create_tables([Object, ObjectDefinition, IgnoredFile])
