import datetime as dt
import functools
import json
from typing import Optional

from configura import config
from flask import request
from marshmallow import Schema, ValidationError
from models.object import Object

from library.types import ErrorCodeType


def create_query_results_response(results: list[tuple[Object, float]]) -> list:
    return [
        {
            **x[0].to_json(),
            "definitions": [y.to_json() for y in x[0].definitions],  # type: ignore
            "distance": x[1],
        }
        for x in results
    ]


def serialize_to_json(obj: Optional[dict] = None) -> Optional[dict]:
    """
    Serialize a dictionary into a JSON serialazble one.
    """

    def serializer(o):
        if isinstance(o, ((dt.datetime, dt.date))):
            return o.isoformat()

        return str(o)

    return json.loads(json.dumps(obj, default=serializer))


def make_response(
    data: Optional[dict] = None,
    status_code: int = 200,
    message: Optional[str] = None,
    page: Optional[int] = None,
    results: Optional[list[dict]] = None,
    page_size: Optional[int] = None,
    pages: Optional[int] = None,
    error: Optional[dict] = None,
    error_code: Optional[ErrorCodeType] = None,
    error_message: Optional[str] = None,
) -> tuple[dict, int]:
    """
    Create a consistent API response.

    Parameters
    ----------
    - `data` : Optional[dict]
        The payload. For consistency, only a dictionary or None is accepted.
        Defaults to None.
    - `status_code` : int
        The response status code. Defaults to 200.
    - `message` : Optional[str]
        A short message describing the response. Defaults to None.
    - `results` : Optional[list[dict]]
        A list of results. If provided, a `results` key is created in the `data`.
        Defaults to None.
    - `page` : Optional[int]
        The current page if pagination for the response exists. Defaults to None.
    - `page_size` : Optional[int]
        The number of items per page if pagination for the response exists. Defaults to None.
    - `pages` : Optional[int]
        The number of pages if pagination for the response exists. Defaults to None.
    - `error` : Optional[dict]
        A dictionary that contains information about the error. For consistency, only a
        dictionary or None is accepted. Defaults to None.
    - `error_code` : Optional[int]
        The error code as per Windows Image Explorer's documentation. Defaults to None.
    - `error_message` : Optional[str]
        A short summary of what the error is about. Defaults to None.

    Notes
    -----
    - If a `error_code` is provided, the fields status_code, message, and error message are
    automatically filled/replaced based on the data from `config/error_codes.json`.
    """

    if error_code:
        message = config.error_codes[error_code]["title"]
        error_message = config.error_codes[error_code]["message"]
        status_code = config.error_codes[error_code]["status_code"]

    if results is not None:
        if data is None:
            data = {}

        data["results"] = results

    if data is not None:
        if page is not None:
            data["page"] = page

        if page_size is not None:
            data["page_size"] = page_size

        if pages is not None:
            data["pages"] = pages

    return {
        "data": serialize_to_json(data),
        "status_code": status_code,
        "message": message,
        "error": error,
        "error_code": error_code,
        "error_message": error_message,
    }, status_code


def body_schema(schema: Schema):
    """
    A route decorator that validates the JSON body with the provided schema.

    Parameters
    ----------
    - `schema` : Schema
        A marshmallow schema.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True)
            if data is None:
                return make_response(error_code="C01")

            try:
                result = schema.load(data)
            except ValidationError as e:
                return make_response(error_code="C02", error={"data": e.messages})

            return func(result, *args, **kwargs)

        return wrapper

    return decorator


def parameters_schema(schema: Schema):
    """
    A route decorator that validates the URL query parameters with the provided schema.

    Parameters
    ----------
    - `schema` : Schema
        A marshmallow schema.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = request.args
            if data is None:
                return make_response(error_code="C03")

            try:
                result = schema.load(data)
            except ValidationError as e:
                return make_response(error_code="C04", error={"data": e.messages})

            return func(result, *args, **kwargs)

        return wrapper

    return decorator
