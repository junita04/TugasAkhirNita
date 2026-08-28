import os, json
os.environ.setdefault("SUPERSET_CONFIG_PATH", "/app/pythonpath/superset_config.py")
from superset.app import create_app
app = create_app()

with app.app_context():
    from superset import db
    from superset.models.slice import Slice

    # Check Classification Report chart fully
    slc = db.session.query(Slice).get(86)
    if slc:
        print(f"Chart id={slc.id}")
        print(f"  slice_name: {slc.slice_name}")
        print(f"  viz_type: {slc.viz_type}")
        print(f"  datasource_type: {slc.datasource_type}")
        print(f"  datasource_id: {slc.datasource_id}")
        params = json.loads(slc.params) if isinstance(slc.params, str) else slc.params
        print(f"  params: {json.dumps(params, indent=2)}")

    # Check all gold-related charts
    print("\n=== All gold-related charts ===")
    for slc in db.session.query(Slice).all():
        params = json.loads(slc.params) if isinstance(slc.params, str) else slc.params
        ds_id = slc.datasource_id
        if ds_id:
            from superset.connectors.sqla.models import SqlaTable
            ds = db.session.query(SqlaTable).get(ds_id)
            if ds and ds.schema == "gold":
                print(f"  id={slc.id} name={slc.slice_name} ds={ds.schema}.{ds.table_name}")
