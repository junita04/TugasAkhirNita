"""
Fix scientific notation for average values in KPI dataset.
"""
import sys, json, requests
sys.path.insert(0, '/app')
from superset.app import create_app
app = create_app()
app.app_context().push()
from superset import db
from superset.connectors.sqla.models import SqlaTable

SUPERSET = 'http://localhost:8088'
r = requests.post(f'{SUPERSET}/api/v1/security/login', json={
    'username': 'admin', 'password': 'change-me', 'provider': 'db', 'refresh': True
})
token = r.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

ds = db.session.query(SqlaTable).filter(SqlaTable.table_name == 'kpi_summary').first()
if ds:
    # Fix: use CAST to DECIMAL before VARCHAR to avoid scientific notation
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
SELECT 'Rata-rata IPK', CAST(CAST(ROUND(CAST(AVG(ipk) AS DOUBLE), 2) AS DECIMAL(10,2)) AS VARCHAR) FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Rata-rata IP', CAST(CAST(ROUND(CAST(AVG(ip) AS DOUBLE), 2) AS DECIMAL(10,2)) AS VARCHAR) FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Rata-rata Total SKS', CAST(CAST(ROUND(CAST(AVG(total_sks) AS DOUBLE), 1) AS DECIMAL(10,1)) AS VARCHAR) FROM iceberg.gold.dim_mahasiswa
"""
    db.session.commit()
    ds.fetch_metadata()
    db.session.commit()
    print("Fixed dataset SQL")

# Validate
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

print("\n=== Validation ===")
for cid, label in kpi_defs:
    r = requests.get(f'{SUPERSET}/api/v1/chart/{cid}/data/', headers=headers, params={'force': 'true'})
    s = db.session.query(Slice).get(cid) if 'Slice' in dir() else None
    if r.status_code == 200:
        data = r.json()
        if 'result' in data and data['result']:
            q = data['result'][0]
            d = q.get('data', [])
            print(f"  ID={cid:3d} {label:35s} data={d[:1]} status={q.get('status')}")
    else:
        err = r.text[:150] if r.text else ""
        print(f"  FAIL  ID={cid:3d} HTTP {r.status_code} {err}")

print(f"\nURL: http://localhost:8088/superset/dashboard/6/")
