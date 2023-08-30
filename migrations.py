import peewee as pw
from playhouse.migrate import SqliteMigrator, migrate

from database import db


def perform_migrations() -> None:
    migrator = SqliteMigrator(db)

    migrate(migrator.add_column("query", "returned_results", pw.IntegerField()))


if __name__ == "__main__":
    perform_migrations()
