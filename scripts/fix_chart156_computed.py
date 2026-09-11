import sys, json, requests
sys.path.insert(0, '/app')
from superset.app import create_app
app = create_app()
app.app_context().push()
from superset import db
from superset.models.slice import Slice
from superset.connectors.sqla.models import SqlaTable, TableColumn

SUPERSET = 'http://localhost:8088'
r = requests.post(f'{SUPERSET}/api/v1/security/login', json={
    'username': 'admin', 'password': 'change-me', 'provider': 'db', 'refresh': True
})
token = r.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# Approach: Add a computed column to dataset ID=27 (dim_mahasiswa)
# that converts empty status_kelulusan to 'Belum Lulus'
dataset = db.session.query(SqlaTable).get(27)
if dataset:
    # Check if computed column already exists
    existing = [c.column_name for c in dataset.columns]
    print(f"Existing columns: {existing}")
    
    if 'status_kelulusan_tampil' not in existing:
        col = TableColumn(
            column_name='status_kelulusan_tampil',
            expression="CASE WHEN status_kelulusan IS NULL OR status_kelulusan = '' THEN 'Belum Lulus' ELSE status_kelulusan END",
            type='VARCHAR',
            table_id=27,
        )
        dataset.columns.append(col)
        db.session.commit()
        print("Added computed column: status_kelulusan_tampil")
    else:
        print("Computed column already exists")

# Now fix chart 156 to use the computed column
s156 = db.session.query(Slice).get(156)
if s156:
    params = {
        "viz_type": "pie",
        "groupby": ["status_kelulusan_tampil"],
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"},
        "row_limit": 100,
        "sort_by_metric": True,
        "show_labels": True,
        "label_type": "key_value_percent",
        "show_legend": True,
    }
    
    qc = {
        "datasource": {"id": 27, "type": "table"},
        "queries": [{
            "columns": ["status_kelulusan_tampil"],
            "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
            "row_limit": 100,
            "orderby": [["Jumlah", False]],
        }],
        "result_format": "json",
        "result_type": "full",
    }
    
    s156.params = json.dumps(params)
    s156.query_context = json.dumps(qc)
    s156.slice_name = "Distribusi Status Kelulusan"
    db.session.commit()
    print("Fixed chart 156 to use computed column")

# Test
r = requests.get(f'{SUPERSET}/api/v1/chart/156/data/', headers=headers, params={'force': 'true'})
print(f"\nChart 156 Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if 'result' in data and data['result']:
        for q in data['result']:
            d = q.get('data', [])
            print(f"Rows: {len(d)}")
            for row in d:
                print(f"  {row}")
else:
    print(f"Error: {r.text[:300]}")
