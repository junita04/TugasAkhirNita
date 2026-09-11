"""
Fix chart 170 - pie chart needs aggregate metric.
"""
import sys
sys.path.insert(0, '/app')

from superset.app import create_app
from superset import db
import json

app = create_app()
app.app_context().push()

from superset.models.slice import Slice

# Fix chart 170: Use COUNT(*) as metric
s170 = db.session.query(Slice).get(170)
s170.params = json.dumps({
    "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"},
    "groupby": ["angkatan"],
    "show_labels": True,
    "label_type": "key_value_percent",
})
s170.query_context = json.dumps({
    "datasource": {"id": 37, "type": "table"},
    "queries": [{"columns": ["angkatan"], "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"}], "row_limit": 10000}],
    "result_format": "json", "result_type": "full",
})
db.session.commit()
print("Fixed chart 170")

# Validate
import requests
SUPERSET = "http://localhost:8088"
r = requests.post(f"{SUPERSET}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
token = r.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

r = requests.get(f"{SUPERSET}/api/v1/chart/170/data/", headers=headers, params={"force": "true"})
s = db.session.query(Slice).get(170)
if r.status_code == 200:
    data = r.json()
    if "result" in data and isinstance(data["result"], list) and len(data["result"]) > 0:
        row_count = len(data["result"][0].get("data", []))
        print(f"  PASS  ID=170  {s.viz_type:25s}  {s.slice_name:35s}  rows={row_count}")
    else:
        print(f"  FAIL  ID=170  empty result")
else:
    print(f"  FAIL  ID=170  HTTP {r.status_code}: {r.text[:200]}")
