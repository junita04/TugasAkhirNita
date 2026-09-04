"""
Fix the 2 failing charts - remove bad filters.
"""
import sys
sys.path.insert(0, '/app')
from superset.app import create_app
from superset import db
import json

app = create_app()
app.app_context().push()

from superset.models.slice import Slice

# Fix chart 156 and 157 - remove the IS NOT NULL filter from query_context
for cid in [156, 157]:
    chart = db.session.query(Slice).get(cid)
    if not chart:
        print(f"Chart {cid}: NOT FOUND")
        continue
    
    # Update query_context - remove filters
    qc = json.loads(chart.query_context) if chart.query_context else {}
    if "queries" in qc and len(qc["queries"]) > 0:
        qc["queries"][0]["filters"] = []
    chart.query_context = json.dumps(qc)
    
    # Also update params - remove adhoc_filters
    params = json.loads(chart.params) if chart.params else {}
    if "adhoc_filters" in params:
        del params["adhoc_filters"]
    chart.params = json.dumps(params)
    
    db.session.commit()
    print(f"Fixed chart {cid} ({chart.slice_name})")

# Test them
import requests
SUPERSET = "http://localhost:8088"
r = requests.post(f"{SUPERSET}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
token = r.json().get("access_token")

for cid in [156, 157]:
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{SUPERSET}/api/v1/chart/{cid}/data/", headers=headers, params={"force": "true"})
    chart = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if "result" in data and isinstance(data["result"], list):
            row_count = len(data["result"][0].get("data", [])) if data["result"] else 0
            print(f"  PASS: Chart {cid} ({chart.slice_name}) rows={row_count}")
        else:
            print(f"  FAIL: Chart {cid} ({chart.slice_name}) empty result")
    else:
        print(f"  FAIL: Chart {cid} ({chart.slice_name}) HTTP {r.status_code}")
