"""
FIX KPI: Increase font size, fix prediction queries, proper number format.
"""
import sys
sys.path.insert(0, '/app')
from superset.app import create_app
from superset import db
import json, requests

app = create_app()
app.app_context().push()

from superset.models.slice import Slice

SUPERSET = "http://localhost:8088"
r = requests.post(f"{SUPERSET}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
token = r.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("FIXING KPI BIG NUMBER CHARTS")
print("=" * 60)

# All KPI chart IDs and their configs
kpi_fixes = {
    # Academic KPIs (from dim_mahasiswa)
    145: {
        "name": "Total Mahasiswa",
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total"},
        "y_axis_format": ",.0f",
    },
    146: {
        "name": "Mahasiswa Aktif",
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN status_mahasiswa='AKTIF' THEN 1 END)", "label": "Aktif"},
        "y_axis_format": ",.0f",
    },
    147: {
        "name": "Mahasiswa Lulus",
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN status_mahasiswa='Lulus' THEN 1 END)", "label": "Lulus"},
        "y_axis_format": ",.0f",
    },
    148: {
        "name": "Tepat Waktu",
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN label=0 THEN 1 END)", "label": "TW"},
        "y_axis_format": ",.0f",
    },
    149: {
        "name": "Terlambat",
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN label=1 THEN 1 END)", "label": "TL"},
        "y_axis_format": ",.0f",
    },
    150: {
        "name": "Rata-rata IPK",
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ipk),2)", "label": "AVG_IPK"},
        "y_axis_format": ",.2f",
    },
    151: {
        "name": "Rata-rata IP",
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ip),2)", "label": "AVG_IP"},
        "y_axis_format": ",.2f",
    },
    152: {
        "name": "Rata-rata Total SKS",
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(AVG(total_sks),1)", "label": "AVG_SKS"},
        "y_axis_format": ",.1f",
    },
    # Prediction KPIs (from model_predictions_v2)
    163: {
        "name": "Total Mahasiswa Diprediksi",
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total"},
        "y_axis_format": ",.0f",
    },
    164: {
        "name": "Prediksi Tepat Waktu",
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN prediksi_label=0 THEN 1 END)", "label": "TW"},
        "y_axis_format": ",.0f",
    },
    165: {
        "name": "Prediksi Terlambat",
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN prediksi_label=1 THEN 1 END)", "label": "TL"},
        "y_axis_format": ",.0f",
    },
    166: {
        "name": "Persentase Tepat Waktu",
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(SUM(CASE WHEN prediksi_label=0 THEN 1 ELSE 0 END)*100.0/COUNT(*),2)", "label": "% TW"},
        "y_axis_format": ",.1f",
    },
    167: {
        "name": "Persentase Terlambat",
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(SUM(CASE WHEN prediksi_label=1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2)", "label": "% TL"},
        "y_axis_format": ",.1f",
    },
}

for cid, cfg in kpi_fixes.items():
    s = db.session.query(Slice).get(cid)
    if not s:
        continue
    
    # Build new params with larger font sizes
    params = {
        "viz_type": "big_number_total",
        "metric": cfg["metric"],
        "header_font_size": 0.8,      # Was 0.4, now 0.8 (large number)
        "subheader_font_size": 0.25,   # Was 0.15, now 0.25 (subtitle)
        "y_axis_format": cfg.get("y_axis_format", ",.0f"),
    }
    
    # Build query_context with proper datasource
    ds_id = 27 if cid <= 152 else 36  # dim_mahasiswa or model_predictions_v2
    ds_type = "table"
    
    params_str = json.dumps(params)
    qc = json.dumps({
        "datasource": {"id": ds_id, "type": ds_type},
        "queries": [{
            "metrics": [cfg["metric"]],
            "row_limit": 1,
        }],
        "result_format": "json",
        "result_type": "full",
    })
    
    s.params = params_str
    s.query_context = qc
    s.slice_name = cfg["name"]
    print(f"  FIXED ID={cid:3d}  {cfg['name']:35s}  header_font=0.8  metric={cfg['metric']['label']}")
    
db.session.commit()

# =====================================================
# Validate all KPI charts
# =====================================================
print("\n" + "=" * 60)
print("VALIDATING KPI CHARTS")
print("=" * 60)

all_kpi = list(kpi_fixes.keys())
for cid in all_kpi:
    r = requests.get(f"{SUPERSET}/api/v1/chart/{cid}/data/", headers=headers, params={"force": "true"})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if "result" in data and isinstance(data["result"], list) and len(data["result"]) > 0:
            result = data["result"][0]
            # Get the actual value
            row = result.get("data", [{}])
            if row:
                val = list(row[0].values())[0] if row else "?"
            else:
                val = "?"
            print(f"  PASS  ID={cid:3d}  {s.slice_name:35s}  value={val}")
        else:
            print(f"  FAIL  ID={cid:3d}  {s.slice_name}  empty result")
    else:
        err = r.text[:100] if r.text else ""
        print(f"  FAIL  ID={cid:3d}  {s.slice_name}  HTTP {r.status_code} {err}")

print(f"\nURL: http://localhost:8088/superset/dashboard/6/")
