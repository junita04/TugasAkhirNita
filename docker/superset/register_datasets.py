import os
from urllib.parse import quote_plus

from superset.app import create_app
from superset.connectors.sqla.models import SqlaTable
from superset.extensions import db
from superset.models.core import Database


TABLES = ("gold_mahasiswa", "gold_program_studi", "gold_kurikulum")


def serving_uri():
    user = quote_plus(os.environ["POSTGRES_USER"])
    password = quote_plus(os.environ["POSTGRES_PASSWORD"])
    database = os.environ["POSTGRES_DB"]
    return f"postgresql+psycopg2://{user}:{password}@postgres:5432/{database}"


app = create_app()
with app.app_context():
    database = db.session.query(Database).filter_by(
        database_name="Academic Serving"
    ).one_or_none()
    if database is None:
        database = Database(
            database_name="Academic Serving",
            sqlalchemy_uri=serving_uri(),
            expose_in_sqllab=True,
        )
        db.session.add(database)
        db.session.flush()

    for table_name in TABLES:
        dataset = db.session.query(SqlaTable).filter_by(
            database_id=database.id,
            table_name=table_name,
            schema="public",
        ).one_or_none()
        if dataset is None:
            db.session.add(SqlaTable(
                database=database,
                table_name=table_name,
                schema="public",
            ))

    db.session.commit()
