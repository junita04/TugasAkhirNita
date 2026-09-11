"""
Convert 8 KPI to horizontal format using table chart.
Two columns: label (left) + value (right) = horizontal card.
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

# 8 KPI definitions with SQL that returns label + value
kpi_defs = {
    145: {
        "name": "Total Mahasiswa",
        "sql": "SELECT 'Total Mahasiswa' AS label, COUNT(*) AS value FROM gold.dim_mahasiswa",
        "fmt": ",.0f",
        "ds": 27,
    },
    146: {
        "name": "Mahasiswa Aktif",
        "sql": "SELECT 'Mahasiswa Aktif' AS label, COUNT(CASE WHEN status_mahasiswa='AKTIF' THEN 1 END) AS value FROM gold.dim_mahasiswa",
        "fmt": ",.0f",
        "ds": 27,
    },
    147: {
        "name": "Mahasiswa Lulus",
        "sql": "SELECT 'Mahasiswa Lulus' AS label, COUNT(CASE WHEN status_mahasiswa='Lulus' THEN 1 END) AS value FROM gold.dim_mahasiswa",
        "fmt": ",.0f",
        "ds": 27,
    },
    148: {
        "name": "Mahasiswa Tepat Waktu",
        "sql": "SELECT 'Mahasiswa Tepat Waktu' AS label, COUNT(CASE WHEN label=0 THEN 1 END) AS value FROM gold.dim_mahasiswa",
        "fmt": ",.0f",
        "ds": 27,
    },
    149: {
        "name": "Mahasiswa Terlambat",
        "sql": "SELECT 'Mahasiswa Terlambat' AS label, COUNT(CASE WHEN label=1 THEN 1 END) AS value FROM gold.dim_mahasiswa",
        "fmt": ",.0f",
        "ds": 27,
    },
    150: {
        "name": "Rata-rata IPK",
        "sql": "SELECT 'Rata-rata IPK' AS label, ROUND(AVG(ipk),2) AS value FROM gold.dim_mahasiswa",
        "fmt": ",.2f",
        "ds": 27,
    },
    151: {
        "name": "Rata-rata IP",
        "sql": "SELECT 'Rata-rata IP' AS label, ROUND(AVG(ip),2) AS value FROM gold.dim_mahasiswa",
        "fmt": ",.2f",
        "ds": 27,
    },
    152: {
        "name": "Rata-rata Total SKS",
        "sql": "SELECT 'Rata-rata Total SKS' AS label, ROUND(AVG(total_sks),1) AS value FROM gold.dim_mahasiswa",
        "fmt": ",.1f",
        "ds": 27,
    },
}

print("Converting 8 KPI to horizontal format...")

for cid, defn in kpi_defs.items():
    s = db.session.query(Slice).get(cid)
    if not s:
        continue
    
    # Use SQL expression to create label + value in one row
    params = {
        "viz_type": "table",
        "all_columns": [],
        "metrics": [{
            "expressionType": "SQL",
            "sqlExpression": defn["sql"],
            "label": defn["name"],
        }],
        "row_limit": 1,
        "include_search": False,
        "page_length": 0,
    }
    
    qc = {
        "datasource": {"id": defn["ds"], "type": "table"},
        "queries": [{
            "metrics": [{
                "expressionType": "SQL",
                "sqlExpression": defn["sql"],
                "label": defn["name"],
            }],
            "row_limit": 1,
        }],
        "result_format": "json",
        "result_type": "full",
    }
    
    s.viz_type = "table"
    s.params = json.dumps(params)
    s.query_context = json.dumps(qc)
    s.slice_name = defn["name"]
    print(f"  ID={cid:3d} {defn['name']:35s}")

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
            print(f"  ID={cid:3d} {s.slice_name:35s} val={val:8} status={status_msg}")
        else:
            print(f"  FAIL  ID={cid:3d} {s.slice_name} empty")
    else:
        err = r.text[:100] if r.text else ""
        print(f"  FAIL  ID={cid:3d} {s.slice_name} HTTP {r.status_code} {err}")

print(f"\nURL: http://localhost:8088/superset/dashboard/6/")
