"""
RESTORE KPIs 146-152 to big_number_total on dim_mahasiswa.
"""
import sys, json, requests
sys.path.insert(0, '/app')
from superset.app import create_app
app = create_app()
app.app_context().push()
from superset import db
from superset.models.slice import Slice

SUPERSET = 'http://localhost:8088'
r = requests.post(f'{SUPERSET}/api/v1/security/login', json={
    'username': 'admin', 'password': 'change-me', 'provider': 'db', 'refresh': True
})
token = r.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# KPI definitions: (chart_id, title, sql_expression, label)
kpi_defs = [
    (146, "Mahasiswa Aktif",
     "COUNT(CASE WHEN status_mahasiswa = 'AKTIF' THEN 1 END)",
     "Mahasiswa Aktif"),
    (147, "Mahasiswa Lulus",
     "COUNT(CASE WHEN status_mahasiswa = 'Lulus' THEN 1 END)",
     "Mahasiswa Lulus"),
    (148, "Mahasiswa Tepat Waktu",
     "COUNT(CASE WHEN status_kelulusan = 'Tepat Waktu' THEN 1 END)",
     "Mahasiswa Tepat Waktu"),
    (149, "Mahasiswa Terlambat",
     "COUNT(CASE WHEN status_kelulusan = 'Terlambat' THEN 1 END)",
     "Mahasiswa Terlambat"),
    (150, "Rata-rata IPK",
     "ROUND(AVG(ipk), 2)",
     "Rata-rata IPK"),
    (151, "Rata-rata IP",
     "ROUND(AVG(ip), 2)",
     "Rata-rata IP"),
    (152, "Rata-rata Total SKS",
     "ROUND(AVG(total_sks), 1)",
     "Rata-rata Total SKS"),
]

for cid, title, sql_expr, label in kpi_defs:
    s = db.session.query(Slice).get(cid)
    if not s:
        print(f"ERROR: chart {cid} not found")
        continue

    metric = {"expressionType": "SQL", "sqlExpression": sql_expr, "label": label}

    params = {
        "viz_type": "big_number_total",
        "metric": metric,
        "header_font_size": 0.6,
        "subheader_font_size": 0.0,
        "y_axis_format": "SMART_NUMBER",
        "time_grain_sqla": "P1D",
        "header_color": "",
        "subheader_color": "",
    }

    qc = {
        "datasource": {"id": 27, "type": "table"},
        "queries": [{
            "metrics": [metric],
            "row_limit": 1,
        }],
        "result_format": "json",
        "result_type": "full",
    }

    s.viz_type = "big_number_total"
    s.datasource_id = 27
    s.datasource_type = "table"
    s.params = json.dumps(params)
    s.query_context = json.dumps(qc)
    print(f"  ID={cid:3d} {title:35s} -> big_number_total, dataset=27")

db.session.commit()

# Validate all
print("\n=== Validation ===")
for cid, title, sql_expr, label in kpi_defs:
    # Also validate 145
    pass

# Validate all 8
all_kpis = [(145, "Total Mahasiswa")] + kpi_defs
for cid, title in all_kpis:
    r = requests.get(f'{SUPERSET}/api/v1/chart/{cid}/data/', headers=headers, params={'force': 'true'})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if 'result' in data and data['result']:
            q = data['result'][0]
            d = q.get('data', [])
            status = q.get('status', 'unknown')
            print(f"  ID={cid:3d} {s.slice_name:35s} data={d[:1]} status={status}")
        else:
            print(f"  FAIL  ID={cid:3d} {s.slice_name} empty result")
    else:
        err = r.text[:150] if r.text else ""
        print(f"  FAIL  ID={cid:3d} HTTP {r.status_code} {err}")

print(f"\nURL: http://localhost:8088/superset/dashboard/6/")
