import os
os.environ.setdefault("SUPERSET_CONFIG_PATH", "/app/pythonpath/superset_config.py")
from superset.app import create_app
app = create_app()
with app.app_context():
    from superset import db
    from superset.connectors.sqla.models import SqlaTable, Database

    trino_db = None
    for d in db.session.query(Database).all():
        if "trino" in (d.sqlalchemy_uri or "").lower():
            trino_db = d
            break
    if not trino_db:
        print("ERROR: No Trino DB"); exit(1)
    print(f"Trino DB id={trino_db.id} name={trino_db.database_name}")

    print("Current datasets:")
    for ds in db.session.query(SqlaTable).all():
        print(f"  id={ds.id} schema={ds.schema} table={ds.table_name}")

    existing = {(ds.schema, ds.table_name) for ds in db.session.query(SqlaTable).all()}
    for table, schema in [("model_metrics_final","gold"),("confusion_matrix_final","gold"),("classification_report_final","gold"),("prediction_by_angkatan_final","gold")]:
        if (schema, table) not in existing:
            ds = SqlaTable(); ds.table_name = table; ds.schema = schema; ds.database_id = trino_db.id
            db.session.add(ds); db.session.flush()
            print(f"  CREATED: {schema}.{table} id={ds.id}")
        else:
            print(f"  EXISTS: {schema}.{table}")
    db.session.commit()

    print("Final datasets:")
    for ds in db.session.query(SqlaTable).all():
        print(f"  id={ds.id} schema={ds.schema} table={ds.table_name}")
