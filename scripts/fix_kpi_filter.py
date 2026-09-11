"""
Fix KPI: Add label filter to each chart, fix scientific notation.
"""
import sys, json, requests
sys.path.insert(0, '/app')
from superset.app import create_app
app = create_app()
app.app_context().push()
from superset import db
from superset.models.slice import Slice
from superset.connectors.sqla.models import SqlaTable

SUPERSET = 'http://localhost:8088'
r = requests.post(f'{SUPERSET}/api/v1/security/login', json={
    'username': 'admin', 'password': 'change-me', 'provider': 'db', 'refresh': True
})
token = r.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# Fix dataset SQL: use proper CAST to avoid scientific notation
ds = db.session.query(SqlaTable).filter(SqlaTable.table_name == 'kpi_summary').first()
if ds:
    ds.sql = """
SELECT 'Total Mahasiswa' AS label, CONCAT(FORMAT_NUMBER(COUNT(*), 0)) AS value FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Mahasiswa Aktif', CONCAT(FORMAT_NUMBER(COUNT(CASE WHEN status_mahasiswa='AKTIF' THEN 1 END), 0)) FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Mahasiswa Lulus', CONCAT(FORMAT_NUMBER(COUNT(CASE WHEN status_mahasiswa='Lulus' THEN 1 END), 0)) FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Mahasiswa Tepat Waktu', CONCAT(FORMAT_NUMBER(COUNT(CASE WHEN label=0 THEN 1 END), 0)) FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Mahasiswa Terlambat', CONCAT(FORMAT_NUMBER(COUNT(CASE WHEN label=1 THEN 1 END), 0)) FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Rata-rata IPK', CAST(CAST(ROUND(AVG(ipk),2) AS DECIMAL(10,2)) AS VARCHAR) FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Rata-rata IP', CAST(CAST(ROUND(AVG(ip),2) AS DECIMAL(10,2)) AS VARCHAR) FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Rata-rata Total SKS', CAST(CAST(ROUND(AVG(total_sks),1) AS DECIMAL(10,1)) AS VARCHAR) FROM iceberg.gold.dim_mahasiswa
"""
    db.session.commit()
    ds.fetch_metadata()
    db.session.commit()
    print(f"Updated dataset SQL")

# Each chart should filter by its specific label
kpi_defs = [
    (145, "Total Mahasiswa"),
    (146, "Mahasiswa Aktif"),
    (147, "Mahasiswa Lulus"),
    (148, "Mahasiswa Tepat Waktu"),
    (149, "Mahasiswa Terlambat"),
    (150, "Rata-rata IPK"),
    (151, "Rata-rata IP"),
    (152, "Rata-rata Total SKS"),
]

for cid, label in kpi_defs:
    s = db.session.query(Slice).get(cid)
    if not s:
        continue
    
    params = {
        "viz_type": "table",
        "all_columns": ["label", "value"],
        "metrics": [],
        "row_limit": 1,
        "include_search": False,
        "page_length": 0,
        "order_desc": False,
        "adhoc_filters": [{
            "clause": "WHERE",
            "expressionType": "SIMPLE",
            "subject": "label",
            "operator": "==",
            "comparator": label,
            "filterOptionName": f"filter_{cid}",
        }],
    }
    
    qc = {
        "datasource": {"id": ds.id, "type": "table"},
        "queries": [{
            "columns": ["label", "value"],
            "metrics": [],
            "row_limit": 1,
            "filters": [{"col": "label", "op": "==", "val": label}],
        }],
        "result_format": "json",
        "result_type": "full",
    }
    
    s.params = json.dumps(params)
    s.query_context = json.dumps(qc)
    print(f"  ID={cid:3d} {label:35s} filter=label='{label}'")

db.session.commit()

# Validate
print("\n=== Validation ===")
for cid, label in kpi_defs:
    r = requests.get(f'{SUPERSET}/api/v1/chart/{cid}/data/', headers=headers, params={'force': 'true'})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if 'result' in data and data['result']:
            q = data['result'][0]
            d = q.get('data', [])
            print(f"  ID={cid:3d} {s.slice_name:35s} data={d[:2]} status={q.get('status')}")
        else:
            print(f"  FAIL  ID={cid:3d} {s.slice_name} empty")
    else:
        err = r.text[:150] if r.text else ""
        print(f"  FAIL  ID={cid:3d} {s.slice_name} HTTP {r.status_code} {err}")

print(f"\nURL: http://localhost:8088/superset/dashboard/6/")
