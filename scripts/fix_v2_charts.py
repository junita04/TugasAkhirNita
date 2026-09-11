"""
Fix chart query_contexts to use lowercase column names.
"""
import sys
sys.path.insert(0, '/app')

from superset.app import create_app
from superset import db
import json

app = create_app()
app.app_context().push()

from superset.models.slice import Slice

# Chart IDs to fix
chart_fixes = {
    168: {  # Distribusi Prediksi (V2) - pie
        "params": {
            "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"},
            "groupby": ["prediksi_label"],
            "show_labels": True,
            "label_type": "key_value_percent",
        },
        "qc": {
            "datasource": {"id": 36, "type": "table"},
            "queries": [{"columns": ["prediksi_label"], "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"}], "row_limit": 10000}],
            "result_format": "json", "result_type": "full",
        },
    },
    169: {  # Prediksi per Angkatan (V2) - bar
        "params": {
            "x_axis": "angkatan",
            "metrics": [
                {"expressionType": "SQL", "sqlExpression": "prediksi_tepat_waktu", "label": "Tepat Waktu"},
                {"expressionType": "SQL", "sqlExpression": "prediksi_terlambat", "label": "Terlambat"},
            ],
            "groupby": [], "stack": True, "show_value": True,
        },
        "qc": {
            "datasource": {"id": 37, "type": "table"},
            "queries": [{"columns": ["angkatan"], "metrics": [{"expressionType": "SQL", "sqlExpression": "prediksi_tepat_waktu", "label": "Tepat Waktu"}, {"expressionType": "SQL", "sqlExpression": "prediksi_terlambat", "label": "Terlambat"}], "row_limit": 10000}],
            "result_format": "json", "result_type": "full",
        },
    },
    170: {  # Persentase per Angkatan (V2) - bar
        "params": {
            "x_axis": "angkatan",
            "metrics": [
                {"expressionType": "SQL", "sqlExpression": "persentase_tepat_waktu", "label": "% Tepat Waktu"},
                {"expressionType": "SQL", "sqlExpression": "persentase_terlambat", "label": "% Terlambat"},
            ],
            "groupby": [], "stack": False, "show_value": True,
        },
        "qc": {
            "datasource": {"id": 37, "type": "table"},
            "queries": [{"columns": ["angkatan"], "metrics": [{"expressionType": "SQL", "sqlExpression": "persentase_tepat_waktu", "label": "% Tepat Waktu"}, {"expressionType": "SQL", "sqlExpression": "persentase_terlambat", "label": "% Terlambat"}], "row_limit": 10000}],
            "result_format": "json", "result_type": "full",
        },
    },
    171: {  # Detail Prediksi Mahasiswa (V2) - table
        "params": {
            "all_columns": ["id_mahasiswa", "angkatan", "ip", "ipk", "total_sks", "jumlah_mk", "selisih_sks", "probabilitas_tepat_waktu", "probabilitas_terlambat", "prediksi_label"],
            "order_by_cols": [],
            "row_limit": 100,
            "page_length": 0,
            "include_search": True,
        },
        "qc": {
            "datasource": {"id": 36, "type": "table"},
            "queries": [{"columns": ["id_mahasiswa", "angkatan", "ip", "ipk", "total_sks", "jumlah_mk", "selisih_sks", "probabilitas_tepat_waktu", "probabilitas_terlambat", "prediksi_label"], "row_limit": 100}],
            "result_format": "json", "result_type": "full",
        },
    },
}

for cid, fix in chart_fixes.items():
    s = db.session.query(Slice).get(cid)
    if s:
        s.params = json.dumps(fix["params"])
        s.query_context = json.dumps(fix["qc"])
        db.session.commit()
        print(f"  Fixed chart {cid}: {s.slice_name}")

print("\nAll charts fixed. Validating...")

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
