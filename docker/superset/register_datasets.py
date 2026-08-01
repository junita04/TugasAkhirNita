from trino_config import (
    TRINO_DATABASE_NAME,
    dataset_specs,
    trino_uri,
)


def register_datasets() -> None:
    from superset.app import create_app
    from superset.connectors.sqla.models import SqlaTable
    from superset.extensions import db
    from superset.models.core import Database

    app = create_app()
    with app.app_context():
        database = db.session.query(Database).filter_by(
            database_name=TRINO_DATABASE_NAME,
        ).one_or_none()
        if database is None:
            database = Database(
                database_name=TRINO_DATABASE_NAME,
                sqlalchemy_uri=trino_uri(),
                expose_in_sqllab=True,
            )
            db.session.add(database)
            db.session.flush()
        elif database.sqlalchemy_uri != trino_uri():
            database.sqlalchemy_uri = trino_uri()

        for schema, table_name in dataset_specs():
            dataset = db.session.query(SqlaTable).filter_by(
                database_id=database.id,
                table_name=table_name,
                schema=schema,
            ).one_or_none()
            if dataset is None:
                db.session.add(
                    SqlaTable(
                        database=database,
                        table_name=table_name,
                        schema=schema,
                    )
                )

        db.session.commit()


if __name__ == "__main__":
    register_datasets()
