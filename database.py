import json

import chromadb
from chromadb.utils import embedding_functions
from configura import config
from peewee import Model, SqliteDatabase, TextField

db = SqliteDatabase(config.main["database"]["sqlite"])
chroma = chromadb.PersistentClient(config.main["database"]["chromadb"])
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=config.main["embeddings_model"]
)


class BaseModel(Model):
    class Meta:
        database = db


class JSONField(TextField):
    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)
