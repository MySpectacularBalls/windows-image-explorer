from typing import Iterable

import peewee as pw
from flask import Blueprint
from flask_restful import Api, Resource
from library import processor_manager
from library.api_utils import (create_query_results_response, make_response,
                               parameters_schema)
from models.query import Query
from schemas.query import (GetQueriesSchema, QueryObjectsSchema,
                           QueryResultsSchema)

app = Blueprint("query", __name__, url_prefix="/api/query")
api = Api(app)


class QueryObjects(Resource):
    method_decorators = {"get": [parameters_schema(schema=QueryObjectsSchema())]}

    def get(self, data: dict):
        """
        Query for objects using similarity search. This is the search function of
        Windows Image Explorer.
        """

        results = processor_manager.query(
            query=data["query"],
            n_results=data["n_results"],
            max_distance=data["max_distance"],
        )

        # Create payload
        payload = create_query_results_response(results)

        return make_response(results=payload)


class Queries(Resource):
    method_decorators = {"get": [parameters_schema(schema=GetQueriesSchema())]}

    def get(self, data: dict):
        """
        Return the user's saved queries.
        """

        # Define the sort functions
        sort_functions = {
            "created_at": Query.created_at,
            "results": Query.returned_results,
        }
        sort_direction_functions = {"descending": "desc", "ascending": "asc"}

        # Get the sort function
        sort = sort_functions.get(data["sort_by"], Query.created_at)
        sort = getattr(
            sort, sort_direction_functions.get(data["sort_direction"], "desc")
        )

        # Get the number of pages
        count = Query.select().count()
        pages = round(count / data["page_size"])

        # Create the payload
        queries = (
            Query.select().order_by(sort()).paginate(data["page"], data["page_size"])
        )
        payload = [x.to_json() for x in queries]

        return make_response(
            results=payload, page=data["page"], page_size=data["page_size"], pages=pages
        )


class QueryResults(Resource):
    method_decorators = {"get": [parameters_schema(QueryResultsSchema())]}

    def get(self, data: dict):
        """
        Get the results of a saved query.
        """

        try:
            query: Query = Query.get(Query.id == data["id"])
        except pw.DoesNotExist:
            return make_response(error_code="C05")

        results = query.results  # type: ignore
        results = create_query_results_response(
            [(x.object, x.distance) for x in results]
        )

        return make_response(results=results)


api.add_resource(QueryObjects, "/")
api.add_resource(Queries, "/queries")
api.add_resource(QueryResults, "/results")


def setup():
    return app
