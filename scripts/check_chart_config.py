import os, json
os.environ.setdefault("SUPERSET_CONFIG_PATH", "/app/pythonpath/superset_config.py")
from superset.app import create_app
app = create_app()

with app.app_context():
    from superset import db
    from superset.models.slice import Slice

    # Find the Classification Report chart
    for slc in db.session.query(Slice).all():
        if "classification" in (slc.slice_name or "").lower() or "Classification" in (slc.slice_name or ""):
            params = json.loads(slc.params) if isinstance(slc.params, str) else slc.params
            print(f"Chart: id={slc.id} name={slc.slice_name} type={slc.viz_type}")
            print(f"  datasource: {params.get('datasource')}")
            print(f"  groupby: {params.get('groupby')}")
            print(f"  metrics: {params.get('metrics')}")
            print(f"  all keys: {list(params.keys())}")
            print()

    # Also check Confusion Matrix chart
    for slc in db.session.query(Slice).all():
        if "confusion" in (slc.slice_name or "").lower():
            params = json.loads(slc.params) if isinstance(slc.params, str) else slc.params
            print(f"Chart: id={slc.id} name={slc.slice_name} type={slc.viz_type}")
            print(f"  datasource: {params.get('datasource')}")
