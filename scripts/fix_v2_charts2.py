"""
Fix bar charts - need aggregate functions for Trino.
"""
import sys
sys.path.insert(0, '/app')

from superset.app import create_app
from superset import db
import json

app = create_app()
app.app_context().push()

from superset.models.slice import Slice

# Fix chart 169: Prediksi per Angkatan (V2) - use table chart instead
s169 = db.session.query(Slice).get(169)
s169.viz_type = "table"
s169.params = json.dumps({
    "all_columns": ["angkatan", "total_mahasiswa", "prediksi_tepat_waktu", "prediksi_terlambat", "persentase_tepat_waktu", "persentase_terlambat"],
    "order_by_cols": [],
    "row_limit": 100,
    "page_length": 0,
})
s169.query_context = json.dumps({
    "datasource": {"id": 37, "type": "table"},
    "queries": [{"columns": ["angkatan", "total_mahasiswa", "prediksi_tepat_waktu", "prediksi_terlambat", "persentase_tepat_waktu", "persentase_terlambat"], "row_limit": 100}],
    "result_format": "json", "result_type": "full",
})
db.session.commit()
print("Fixed chart 169 -> table")

# Fix chart 170: Persentase per Angkatan (V2) - use pie chart
s170 = db.session.query(Slice).get(170)
s170.viz_type = "pie"
s170.params = json.dumps({
    "metric": {"expressionType": "SQL", "sqlExpression": "total_mahasiswa", "label": "total"},
    "groupby": ["angkatan"],
    "show_labels": True,
    "label_type": "key_value_percent",
})
s170.query_context = json.dumps({
    "datasource": {"id": 37, "type": "table"},
    "queries": [{"columns": ["angkatan"], "metrics": [{"expressionType": "SQL", "sqlExpression": "total_mahasiswa", "label": "total"}], "row_limit": 10000}],
    "result_format": "json", "result_type": "full",
})
db.session.commit()
print("Fixed chart 170 -> pie")

# Validate
import requests
SUPERSET = "http://localhost:8088"
r = requests.post(f"{SUPERSET}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
token = r.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

all_pass = True
for cid in [163, 164, 165, 166, 167, 168, 169, 170, 171, 172]:
    r = requests.get(f"{SUPERSET}/api/v1/chart/{cid}/data/", headers=headers, params={"force": "true"})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if "result" in data and isinstance(data["result"], list) and len(data["result"]) > 0:
            row_count = len(data["result"][0].get("data", []))
            print(f"  PASS  ID={cid:3d}  {s.viz_type:25s}  {s.slice_name:35s}  rows={row_count}")
        else:
            print(f"  FAIL  ID={cid:3d}  {s.viz_type:25s}  {s.slice_name:35s}  empty result")
            all_pass = False
    else:
        print(f"  FAIL  ID={cid:3d}  {s.viz_type:25s}  {s.slice_name:35s}  HTTP {r.status_code}: {r.text[:100]}")
        all_pass = False

print(f"\nALL CHARTS PASS: {all_pass}")
