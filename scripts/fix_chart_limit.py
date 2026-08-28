import os, json
os.environ.setdefault("SUPERSET_CONFIG_PATH", "/app/pythonpath/superset_config.py")
from superset.app import create_app
app = create_app()

with app.app_context():
    from superset import db
    from superset.models.slice import Slice

    slc = db.session.query(Slice).get(86)
    if slc:
        params = json.loads(slc.params) if isinstance(slc.params, str) else slc.params
        old_limit = params.get("row_limit")
        params["row_limit"] = 100
        slc.params = json.dumps(params)
        db.session.commit()
        print(f"Updated Classification Report row_limit: {old_limit} -> 100")
    else:
        print("Chart not found")
