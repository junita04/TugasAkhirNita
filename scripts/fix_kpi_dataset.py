"""
Fix KPI dataset: remove sort_order, use label ordering instead.
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

# Update the virtual dataset SQL without sort_order
ds = db.session.query(SqlaTable).filter(SqlaTable.table_name == 'kpi_summary').first()
if ds:
    ds.sql = """
SELECT 'Total Mahasiswa' AS label, CAST(COUNT(*) AS VARCHAR) AS value FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Mahasiswa Aktif', CAST(COUNT(CASE WHEN status_mahasiswa='AKTIF' THEN 1 END) AS VARCHAR) FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Mahasiswa Lulus', CAST(COUNT(CASE WHEN status_mahasiswa='Lulus' THEN 1 END) AS VARCHAR) FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Mahasiswa Tepat Waktu', CAST(COUNT(CASE WHEN label=0 THEN 1 END) AS VARCHAR) FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Mahasiswa Terlambat', CAST(COUNT(CASE WHEN label=1 THEN 1 END) AS VARCHAR) FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Rata-rata IPK', CAST(ROUND(AVG(ipk),2) AS VARCHAR) FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Rata-rata IP', CAST(ROUND(AVG(ip),2) AS VARCHAR) FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Rata-rata Total SKS', CAST(ROUND(AVG(total_sks),1) AS VARCHAR) FROM iceberg.gold.dim_mahasiswa
"""
    db.session.commit()
    ds.fetch_metadata()
    db.session.commit()
    print(f"Updated dataset SQL (id={ds.id})")
    print(f"Columns: {[c.column_name for c in ds.columns]}")

# Update all 8 KPI charts to use simple query without sort_order
kpi_ids = [145, 146, 147, 148, 149, 150, 151, 152]
for cid in kpi_ids:
    s = db.session.query(Slice).get(cid)
    if not s:
        continue
    
    params = {
        "viz_type": "table",
        "all_columns": ["label", "value"],
        "metrics": [],
        "row_limit": 8,
        "include_search": False,
        "page_length": 0,
        "order_desc": False,
    }
    
    qc = {
        "datasource": {"id": ds.id, "type": "table"},
        "queries": [{
            "columns": ["label", "value"],
            "metrics": [],
            "row_limit": 8,
        }],
        "result_format": "json",
        "result_type": "full",
    }
    
    s.params = json.dumps(params)
    s.query_context = json.dumps(qc)
    print(f"  ID={cid:3d} {s.slice_name:35s} updated")

db.session.commit()

# Validate
print("\n=== Validation ===")
for cid in kpi_ids:
    r = requests.get(f'{SUPERSET}/api/v1/chart/{cid}/data/', headers=headers, params={'force': 'true'})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if 'result' in data and data['result']:
            q = data['result'][0]
            d = q.get('data', [])
            cols = q.get('colnames', [])
            print(f"  ID={cid:3d} {s.slice_name:35s} cols={cols} data={d[:2]} status={q.get('status')}")
        else:
            print(f"  FAIL  ID={cid:3d} {s.slice_name} empty")
    else:
        err = r.text[:150] if r.text else ""
        print(f"  FAIL  ID={cid:3d} {s.slice_name} HTTP {r.status_code} {err}")

print(f"\nURL: http://localhost:8088/superset/dashboard/6/")
