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

# Fix chart 156 - use proper query_context format
s156 = db.session.query(Slice).get(156)
if s156:
    params = {
        "viz_type": "pie",
        "groupby": ["status_kelulusan_clean"],
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"},
        "row_limit": 100,
        "sort_by_metric": True,
        "innerRadius": 30,
        "outerRadius": 70,
        "show_labels": True,
        "labelsOutside": True,
        "label_type": "key_percent",
        "show_legend": True,
    }
    
    # The column needs to be in a SQL expression in the query
    # Use adhoc_metric or simple approach
    qc = {
        "datasource": {"id": 27, "type": "table"},
        "queries": [{
            "columns": [],
            "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN status_kelulusan IS NULL OR status_kelulusan = '' THEN 'Belum Lulus' ELSE status_kelulusan END)", "label": "Jumlah"}],
            "row_limit": 100,
            "orderby": [["Jumlah", False]],
        }],
        "result_format": "json",
        "result_type": "full",
    }
    
    s156.params = json.dumps(params)
    s156.query_context = json.dumps(qc)
    print("Fixed chart 156 query_context")
    db.session.commit()

# Test
r = requests.get(f'{SUPERSET}/api/v1/chart/156/data/', headers=headers, params={'force': 'true'})
print(f"Status: {r.status_code}")
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
