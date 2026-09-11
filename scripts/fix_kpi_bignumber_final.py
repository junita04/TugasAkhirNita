"""
FIX 8 KPI: Convert back to big_number_total with simplest config.
big_number_total is the native KPI viz - it should work.
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

# 8 KPI definitions
kpi_defs = {
    145: {"name": "Total Mahasiswa", "sql": "COUNT(*)", "fmt": ",.0f", "ds": 27},
    146: {"name": "Mahasiswa Aktif", "sql": "COUNT(CASE WHEN status_mahasiswa='AKTIF' THEN 1 END)", "fmt": ",.0f", "ds": 27},
    147: {"name": "Mahasiswa Lulus", "sql": "COUNT(CASE WHEN status_mahasiswa='Lulus' THEN 1 END)", "fmt": ",.0f", "ds": 27},
    148: {"name": "Mahasiswa Tepat Waktu", "sql": "COUNT(CASE WHEN label=0 THEN 1 END)", "fmt": ",.0f", "ds": 27},
    149: {"name": "Mahasiswa Terlambat", "sql": "COUNT(CASE WHEN label=1 THEN 1 END)", "fmt": ",.0f", "ds": 27},
    150: {"name": "Rata-rata IPK", "sql": "ROUND(AVG(ipk),2)", "fmt": ",.2f", "ds": 27},
    151: {"name": "Rata-rata IP", "sql": "ROUND(AVG(ip),2)", "fmt": ",.2f", "ds": 27},
    152: {"name": "Rata-rata Total SKS", "sql": "ROUND(AVG(total_sks),1)", "fmt": ",.1f", "ds": 27},
}

print("Converting 8 KPI to big_number_total with simplest config...")

for cid, defn in kpi_defs.items():
    s = db.session.query(Slice).get(cid)
    if not s:
        continue
    
    metric = {"expressionType": "SQL", "sqlExpression": defn["sql"], "label": defn["name"]}
    
    # Simplest possible big_number_total config
    params = {
        "viz_type": "big_number_total",
        "metric": metric,
        "header_font_size": 0.4,
        "subheader_font_size": 0.0,
        "y_axis_format": defn["fmt"],
    }
    
    qc = {
        "datasource": {"id": defn["ds"], "type": "table"},
        "queries": [{
            "metrics": [metric],
            "row_limit": 1,
        }],
        "result_format": "json",
        "result_type": "full",
    }
    
    s.viz_type = "big_number_total"
    s.params = json.dumps(params)
    s.query_context = json.dumps(qc)
    s.slice_name = defn["name"]
    print(f"  ID={cid:3d} {defn['name']:35s} big_number_total hfs=0.4")

db.session.commit()

# Validate
print("\n=== Validation ===")
for cid, defn in kpi_defs.items():
    r = requests.get(f'{SUPERSET}/api/v1/chart/{cid}/data/', headers=headers, params={'force': 'true'})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if 'result' in data and data['result']:
            row = data['result'][0].get('data', [{}])
            val = list(row[0].values())[0] if row else '?'
            status_msg = data['result'][0].get('status', '?')
            error = data['result'][0].get('error')
            print(f"  ID={cid:3d} {s.slice_name:35s} val={val:8} status={status_msg} error={error}")
        else:
            print(f"  FAIL  ID={cid:3d} {s.slice_name} empty")
    else:
        print(f"  FAIL  ID={cid:3d} {s.slice_name} HTTP {r.status_code}")

print(f"\nURL: http://localhost:8088/superset/dashboard/6/")
