from superset.app import create_app

from trino_config import TRINO_DATABASE_NAME, dataset_specs, trino_uri


app = create_app()
from superset.connectors.sqla.models import SqlaTable  # noqa: E402
from superset.extensions import db  # noqa: E402
from superset.models.core import Database  # noqa: E402


def register_trino_database():
    with app.app_context():
        database = db.session.query(Database).filter_by(
            database_name=TRINO_DATABASE_NAME
        ).one_or_none()
        if database is None:
            database = Database(
                database_name=TRINO_DATABASE_NAME,
                sqlalchemy_uri=trino_uri(),
                expose_in_sqllab=True,
                allow_dml=False,
            )
            db.session.add(database)
            db.session.flush()

        for schema, table_name in dataset_specs():
            dataset = db.session.query(SqlaTable).filter_by(
                database_id=database.id,
                table_name=table_name,
                schema=schema,
            ).one_or_none()
            if dataset is None:
                db.session.add(SqlaTable(
                    database=database,
                    table_name=table_name,
                    schema=schema,
                ))

        db.session.commit()
        print(f"Registered Trino database: {TRINO_DATABASE_NAME}")


if __name__ == "__main__":
    register_trino_database()
