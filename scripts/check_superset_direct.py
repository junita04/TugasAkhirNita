import os, json
os.environ.setdefault("SUPERSET_CONFIG_PATH", "/app/pythonpath/superset_config.py")
from superset.app import create_app
app = create_app()

with app.app_context():
    from superset import db
    from superset.connectors.sqla.models import SqlaTable
    from superset.models.dashboard import Dashboard
    from superset.models.slice import Slice

    # Dashboard
    dash = db.session.query(Dashboard).get(3)
    if dash:
        print(f"Dashboard: {dash.dashboard_title}")
        print(f"Published: {dash.published}")
    else:
        print("Dashboard id=3 NOT FOUND")
        for d in db.session.query(Dashboard).all():
            print(f"  id={d.id} {d.dashboard_title}")

    # Gold datasets
    print("\nGold datasets:")
    for ds in db.session.query(SqlaTable).filter(SqlaTable.schema == "gold").all():
        print(f"  id={ds.id} {ds.schema}.{ds.table_name}")

    # Charts
    print("\nAll charts:")
    for slc in db.session.query(Slice).all():
        print(f"  id={slc.id} {slc.slice_name} type={slc.viz_type}")
