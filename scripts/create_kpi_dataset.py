"""
Create virtual dataset for horizontal KPI display.
Uses SQL query to return label + value pairs.
"""
import sys, json, requests
sys.path.insert(0, '/app')
from superset.app import create_app
app = create_app()
app.app_context().push()
from superset import db
from superset.models.slice import Slice
from superset.connectors.sqla.models import SqlaTable, TableColumn
from superset.models.core import Database

SUPERSET = 'http://localhost:8088'
r = requests.post(f'{SUPERSET}/api/v1/security/login', json={
    'username': 'admin', 'password': 'change-me', 'provider': 'db', 'refresh': True
})
token = r.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# Find the Trino database connection
trino_db = db.session.query(Database).filter(Database.database_name == 'Academic Trino').first()
if not trino_db:
    # Try other names
    for name in ['Academic Trino', 'trino', 'Trino', 'iceberg']:
        trino_db = db.session.query(Database).filter(Database.database_name == name).first()
        if trino_db:
            break

if trino_db:
    print(f"Found database: {trino_db.database_name} (id={trino_db.id})")
else:
    print("ERROR: Trino database not found")
    # List all databases
    for d in db.session.query(Database).all():
        print(f"  {d.database_name} (id={d.id})")

# Check if dataset "kpi_summary" already exists
existing = db.session.query(SqlaTable).filter(SqlaTable.table_name == 'kpi_summary').first()
if existing:
    print(f"Dataset 'kpi_summary' already exists (id={existing.id})")
    kpi_dataset_id = existing.id
else:
    print("Creating virtual dataset 'kpi_summary'...")
    
    # SQL query that returns all 8 KPIs as rows
    sql = """
SELECT 'Total Mahasiswa' AS label, CAST(COUNT(*) AS VARCHAR) AS value, 1 AS sort_order FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Mahasiswa Aktif', CAST(COUNT(CASE WHEN status_mahasiswa='AKTIF' THEN 1 END) AS VARCHAR), 2 FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Mahasiswa Lulus', CAST(COUNT(CASE WHEN status_mahasiswa='Lulus' THEN 1 END) AS VARCHAR), 3 FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Mahasiswa Tepat Waktu', CAST(COUNT(CASE WHEN label=0 THEN 1 END) AS VARCHAR), 4 FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Mahasiswa Terlambat', CAST(COUNT(CASE WHEN label=1 THEN 1 END) AS VARCHAR), 5 FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Rata-rata IPK', CAST(ROUND(AVG(ipk),2) AS VARCHAR), 6 FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Rata-rata IP', CAST(ROUND(AVG(ip),2) AS VARCHAR), 7 FROM iceberg.gold.dim_mahasiswa
UNION ALL
SELECT 'Rata-rata Total SKS', CAST(ROUND(AVG(total_sks),1) AS VARCHAR), 8 FROM iceberg.gold.dim_mahasiswa
ORDER BY sort_order
"""
    
    ds = SqlaTable(
        table_name='kpi_summary',
        database_id=trino_db.id,
        sql=sql,
        schema='gold',
    )
    db.session.add(ds)
    db.session.commit()
    
    # Refresh to get column info
    ds.fetch_metadata()
    db.session.commit()
    
    kpi_dataset_id = ds.id
    print(f"Created dataset 'kpi_summary' (id={kpi_dataset_id})")
    print(f"Columns: {[c.column_name for c in ds.columns]}")

# Now create/update the 8 KPI charts to use this dataset
kpi_defs = [
    (145, "Total Mahasiswa", 1),
    (146, "Mahasiswa Aktif", 2),
    (147, "Mahasiswa Lulus", 3),
    (148, "Mahasiswa Tepat Waktu", 4),
    (149, "Mahasiswa Terlambat", 5),
    (150, "Rata-rata IPK", 6),
    (151, "Rata-rata IP", 7),
    (152, "Rata-rata Total SKS", 8),
]

print("\nConfiguring 8 KPI charts...")

for cid, name, sort_order in kpi_defs:
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
        "order_by_cols": [json.dumps(["sort_order", True])],
    }
    
    qc = {
        "datasource": {"id": kpi_dataset_id, "type": "table"},
        "queries": [{
            "columns": ["label", "value"],
            "metrics": [],
            "row_limit": 1,
            "orderby": [["sort_order", True]],
        }],
        "result_format": "json",
        "result_type": "full",
    }
    
    s.viz_type = "table"
    s.datasource_id = kpi_dataset_id
    s.datasource_type = "table"
    s.params = json.dumps(params)
    s.query_context = json.dumps(qc)
    s.slice_name = name
    print(f"  ID={cid:3d} {name:35s} -> kpi_summary dataset")

db.session.commit()

# Validate
print("\n=== Validation ===")
for cid, name, sort_order in kpi_defs:
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
