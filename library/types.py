from typing import Literal, cast, get_args

ObjectType = Literal["image"]
ErrorLogType = Literal[
    "processing-object-failed",
    "resolution-not-found",
    "decompression-bomb-error",
    "object-not-found-while-querying",
]
ErrorCodeType = Literal["C01", "C02", "C03", "C04", "C05"]
DefinitionType = Literal["image-description"]
TimeMetricType = Literal["generate-image-caption", "query", "generate-embeddings"]
IgnoredFileType = Literal["decompression-bomb-error", "invalid-file"]

definition_types = [
    (cast(str, value), cast(str, value)) for value in get_args(DefinitionType)
]
object_types = [(cast(str, value), cast(str, value)) for value in get_args(ObjectType)]
error_log_types = [
    (cast(str, value), cast(str, value)) for value in get_args(ErrorLogType)
]
ignored_file_types = [
    (cast(str, value), cast(str, value)) for value in get_args(IgnoredFileType)
]
time_metric_types = [
    (cast(str, value), cast(str, value)) for value in get_args(TimeMetricType)
]
