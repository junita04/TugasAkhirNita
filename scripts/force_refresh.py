"""
Force dashboard refresh - update timestamps and clear cache.
"""
import sys
sys.path.insert(0, '/app')
from superset.app import create_app
from superset import db, cache
from datetime import datetime
import json

app = create_app()
app.app_context().push()

from superset.models.dashboard import Dashboard
from superset.models.slice import Slice
from superset.connectors.sqla.models import SqlaTable

dash = db.session.query(Dashboard).get(4)

# Force update changed_on
dash.changed_on = datetime.utcnow()
dash.changed_by_fk = 1  # admin user

# Re-save position_json to force re-parse
pos = json.loads(dash.position_json)
dash.position_json = json.dumps(pos)

db.session.commit()

# Try to clear Superset caches
try:
    cache.clear()
    print("Cache cleared")
except:
    print("Cache clear skipped")

# Verify
dash2 = db.session.query(Dashboard).get(4)
pos2 = json.loads(dash2.position_json)
chart_count = sum(1 for k in pos2 if k.startswith("CHART-"))
print(f"Dashboard: {dash2.dashboard_title}")
print(f"Charts in layout: {chart_count}")
print(f"Changed on: {dash2.changed_on}")

# List all charts
for k, v in sorted(pos2.items()):
    if k.startswith("CHART-"):
        cid = v.get("meta", {}).get("chartId")
        s = db.session.query(Slice).get(cid)
        if s:
            print(f"  {k}: chartId={cid} name={s.slice_name} params_len={len(s.params) if s.params else 0}")
        else:
            print(f"  {k}: chartId={cid} MISSING!")

print(f"\nURL: http://localhost:8088/superset/dashboard/4/?force=true")
print("DONE")
