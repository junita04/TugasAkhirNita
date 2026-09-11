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

# Chart 156: Use simple groupby with status_kelulusan
# The empty string will show as empty label, but no <NULL> error
s156 = db.session.query(Slice).get(156)
if s156:
    params = {
        "viz_type": "pie",
        "groupby": ["status_kelulusan"],
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
    
    qc = {
        "datasource": {"id": 27, "type": "table"},
        "queries": [{
            "columns": ["status_kelulusan"],
            "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
            "row_limit": 100,
            "orderby": [["Jumlah", False]],
        }],
        "result_format": "json",
        "result_type": "full",
    }
    
    s156.params = json.dumps(params)
    s156.query_context = json.dumps(qc)
    db.session.commit()
    print("Fixed chart 156: simple groupby status_kelulusan")

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
