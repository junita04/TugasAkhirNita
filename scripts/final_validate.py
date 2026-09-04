"""
Final validation of all charts in Dashboard 5.
"""
import requests
import json
import sys
sys.path.insert(0, '/app')
from superset.app import create_app
from superset import db
app = create_app()
app.app_context().push()
from superset.models.slice import Slice

SUPERSET = "http://localhost:8088"
r = requests.post(f"{SUPERSET}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
token = r.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Get all charts from dashboard 5
from superset.models.dashboard import Dashboard
dash = db.session.query(Dashboard).get(5)
pos = json.loads(dash.position_json) if dash.position_json else {}
chart_ids = [v.get("meta", {}).get("chartId") for k, v in pos.items() if k.startswith("CHART-")]

print("=" * 70)
print("FINAL CHART VALIDATION - DASHBOARD 5")
print("=" * 70)
print(f"Total charts: {len(chart_ids)}\n")

all_pass = True
for cid in chart_ids:
    r = requests.get(f"{SUPERSET}/api/v1/chart/{cid}/data/", headers=headers, params={"force": "true"})
    chart = db.session.query(Slice).get(cid)
    name = chart.slice_name if chart else "?"
    viz = chart.viz_type if chart else "?"
    
    if r.status_code == 200:
        data = r.json()
        if "result" in data and isinstance(data["result"], list) and len(data["result"]) > 0:
            row_count = len(data["result"][0].get("data", []))
            print(f"  PASS  ID={cid:3d}  {viz:25s}  {name:35s}  rows={row_count}")
        else:
            print(f"  FAIL  ID={cid:3d}  {viz:25s}  {name:35s}  empty result")
            all_pass = False
    else:
        error = r.text[:60] if r.text else ""
        print(f"  FAIL  ID={cid:3d}  {viz:25s}  {name:35s}  HTTP {r.status_code}: {error}")
        all_pass = False

print(f"\n{'='*70}")
print(f"ALL CHARTS PASS: {all_pass}")
print(f"DASHBOARD: http://localhost:8088/superset/dashboard/5/")
print(f"{'='*70}")
