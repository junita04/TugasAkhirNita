import os, json
os.environ.setdefault("SUPERSET_CONFIG_PATH", "/app/pythonpath/superset_config.py")
from superset.app import create_app
app = create_app()

with app.app_context():
    from superset import db
    from superset.connectors.sqla.models import SqlaTable

    # Find the classification_report_final dataset
    ds = db.session.query(SqlaTable).filter_by(
        schema="gold", table_name="classification_report_final"
    ).first()

    if ds:
        print(f"Found dataset: id={ds.id} {ds.schema}.{ds.table_name}")
        # Fetch fresh metadata from Trino
        ds.fetch_metadata()
        db.session.commit()
        print("Metadata refreshed!")
        print(f"Columns: {[col.column_name for col in ds.columns]}")
    else:
        print("Dataset not found!")
        for d in db.session.query(SqlaTable).filter(SqlaTable.schema == "gold").all():
            print(f"  id={d.id} {d.schema}.{d.table_name}")
