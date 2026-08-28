import os, json
os.environ.setdefault("SUPERSET_CONFIG_PATH", "/app/pythonpath/superset_config.py")
from superset.app import create_app
app = create_app()

with app.app_context():
    from superset import db
    from superset.connectors.sqla.models import SqlaTable

    # Step 1: Delete the duplicate _final datasets (ids 23-26)
    for ds_id in [23, 24, 25, 26]:
        ds = db.session.query(SqlaTable).get(ds_id)
        if ds:
            print(f"  Deleting duplicate: id={ds.id} {ds.schema}.{ds.table_name}")
            db.session.delete(ds)
    db.session.commit()
    print("Duplicates deleted")

    # Step 2: Rename old datasets
    rename_map = {
        "model_metrics": "model_metrics_final",
        "confusion_matrix": "confusion_matrix_final",
        "classification_report": "classification_report_final",
        "prediction_by_angkatan": "prediction_by_angkatan_final",
    }

    for old_name, new_name in rename_map.items():
        ds = db.session.query(SqlaTable).filter_by(
            schema="gold", table_name=old_name
        ).first()
        if ds:
            ds.table_name = new_name
            print(f"  Renamed: gold.{old_name} -> gold.{new_name} (id={ds.id})")

    db.session.commit()
    print("Renames done")

    # Step 3: Refresh metadata
    for new_name in rename_map.values():
        ds = db.session.query(SqlaTable).filter_by(
            schema="gold", table_name=new_name
        ).first()
        if ds:
            try:
                ds.fetch_metadata()
                db.session.commit()
                print(f"  Refreshed: gold.{new_name}")
            except Exception as e:
                print(f"  Refresh error for {new_name}: {e}")
                db.session.rollback()

    # Final state
    print("\nFinal gold datasets:")
    for ds in db.session.query(SqlaTable).filter(SqlaTable.schema == "gold").all():
        print(f"  id={ds.id} gold.{ds.table_name}")
