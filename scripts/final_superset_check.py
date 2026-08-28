import os, json
os.environ.setdefault("SUPERSET_CONFIG_PATH", "/app/pythonpath/superset_config.py")
from superset.app import create_app
app = create_app()

with app.app_context():
    from superset import db
    from superset.models.slice import Slice
    from superset.connectors.sqla.models import SqlaTable

    print("=== Dashboard Charts Status ===")
    for slc in db.session.query(Slice).all():
        ds_id = slc.datasource_id
        ds_name = "N/A"
        if ds_id:
            ds = db.session.query(SqlaTable).get(ds_id)
            if ds:
                ds_name = f"{ds.schema}.{ds.table_name}"
        print(f"  id={slc.id:3d} | {slc.slice_name:45s} | type={slc.viz_type:25s} | ds={ds_name}")

    # Verify classification_report_final columns
    print("\n=== Classification Report Dataset Columns ===")
    ds = db.session.query(SqlaTable).filter_by(
        schema="gold", table_name="classification_report_final"
    ).first()
    if ds:
        cols = [col.column_name for col in ds.columns]
        print(f"  Columns: {cols}")
        has_class = "class" in cols
        print(f"  'class' column present: {has_class}")
