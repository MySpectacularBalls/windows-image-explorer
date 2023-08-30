import os
import string
from typing import Optional

from configura import config
from models.error import Error
from models.metric import TimeMetric
from PIL import Image

from .types import ErrorLogType, ObjectType, TimeMetricType


def get_drives() -> list[str]:
    """
    Returns a list of drives available in this device.
    """

    drives = []
    for drive in string.ascii_uppercase:
        if os.path.exists(drive + ":\\"):
            drives.append(drive + ":\\")

    return drives


def log_error(
    type: ErrorLogType,
    title: str,
    message: Optional[str] = None,
    traceback: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Error:
    """
    Log an error into the database.
    """

    return Error.create(
        type=type, title=title, message=message, traceback=traceback, metadata=metadata
    )


def log_time_metric(
    type: TimeMetricType,
    tt: float,
    title: Optional[str] = None,
    message: Optional[str] = None,
) -> None:
    """
    Logs a time metric into the database.
    """

    return TimeMetric.create(type=type, tt=tt, title=title, message=message)


def get_file_id(path: str) -> str:
    """
    Get the ID of a file. Derived from `st_dev` and `st_ino`.

    Parameters
    ----------
    `path` : str
        The path to the file.

    Returns
    -------
    `str`
    """

    file_stat = os.stat(path)
    return f"{file_stat.st_dev}-{file_stat.st_ino}"


def get_object_type_from_file(path: str) -> Optional[ObjectType]:
    """
    Parameters
    ----------
    `path` : str
        The path to the file.

    Returns
    -------
    `Optional[ObjectType]`
    """

    _, ext = os.path.splitext(path)
    ext = ext.lower()

    for type in config.types:
        if ext in type["file_extensions"]:
            return type["type"]


def get_image_resolution(path: str) -> Optional[tuple[int, int]]:
    """
    Get the resolution of an image.

    Parameters
    ----------
    `path` : str
        The path to the image file.

    Returns
    -------
    `Optional[tuple[int, int]]` :
        The resolution in (w, h) or None if parsing the image file fails.
    """

    try:
        with Image.open(path, "r") as image:
            image: Image.Image

            width, height = image.size
            return width, height
    except IOError:
        return
