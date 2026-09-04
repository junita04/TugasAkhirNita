"""
Fresh audit - check actual state of Dashboard 4.
"""
import sys
sys.path.insert(0, '/app')
from superset.app import create_app
from superset import db
import json

app = create_app()
app.app_context().push()

from superset.models.dashboard import Dashboard
from superset.models.slice import Slice
from superset.connectors.sqla.models import SqlaTable

# 1. Get dashboard
dash = db.session.query(Dashboard).get(4)
print(f"Dashboard: {dash.dashboard_title}")
print(f"Published: {dash.published}")

# 2. Parse position_json
pos = json.loads(dash.position_json) if dash.position_json else {}

# 3. Find ALL CHART-* keys
chart_keys = {k: v for k, v in pos.items() if k.startswith("CHART-")}
print(f"\nTotal CHART-* keys in position_json: {len(chart_keys)}")

# 4. For each CHART key, check if the chartId exists in Slice table
valid = 0
invalid = 0
for key, val in sorted(chart_keys.items()):
    cid = val.get("meta", {}).get("chartId")
    slice_obj = db.session.query(Slice).get(cid) if cid else None
    if slice_obj:
        valid += 1
        ds = db.session.query(SqlaTable).get(slice_obj.datasource_id)
        ds_name = ds.table_name if ds else "NO_DATASET"
        print(f"  OK   {key} -> chartId={cid} name={slice_obj.slice_name} dataset={ds_name}")
    else:
        invalid += 1
        print(f"  FAIL {key} -> chartId={cid} DOES NOT EXIST")

print(f"\nValid: {valid}, Invalid: {invalid}")

# 5. Check ALL slices in DB
all_slices = db.session.query(Slice).all()
print(f"\nTotal slices in DB: {len(all_slices)}")

# 6. Check which slices reference dataset 27
ds27_slices = db.session.query(Slice).filter(Slice.datasource_id == 27).all()
print(f"Slices using dataset 27 (dim_mahasiswa): {len(ds27_slices)}")
for s in ds27_slices:
    print(f"  ID={s.id} Name={s.slice_name}")

# 7. Check native filters
print(f"\nNative filters (json_metadata):")
meta = json.loads(dash.json_metadata) if dash.json_metadata else {}
print(f"  {json.dumps(meta, indent=2)[:500]}")
