from marshmallow import Schema, fields, validate


class PagingSchema(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Int(load_default=25, validate=validate.Range(min=1, max=255))


class QueryObjectsSchema(Schema):
    query = fields.Str(required=True, validate=validate.Length(min=1, max=1024))
    n_results = fields.Int(load_default=35, validate=validate.Range(min=1, max=150))
    max_distance = fields.Float(load_default=None)


class GetQueriesSchema(PagingSchema):
    sort_by = fields.Str(
        load_default="created_at", validate=validate.OneOf(["created_at", "results"])
    )
    sort_direction = fields.Str(
        load_default="descending", validate=validate.OneOf(["descending", "ascending"])
    )


class QueryResultsSchema(PagingSchema):
    id = fields.Str()
