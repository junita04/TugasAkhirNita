"""
Test: Check which viz types render without warnings in small cards.
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

# Test chart 145 with different viz types
s = db.session.query(Slice).get(145)
orig_viz = s.viz_type
orig_params = s.params
orig_qc = s.query_context

metric = {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total Mahasiswa"}

# Test 1: big_number_total (original)
print("=== Test 1: big_number_total ===")
params_bn = {
    "viz_type": "big_number_total",
    "metric": metric,
    "header_font_size": 0.4,
    "subheader_font_size": 0.0,
    "y_axis_format": ",.0f",
}
qc = {
    "datasource": {"id": 27, "type": "table"},
    "queries": [{"metrics": [metric], "row_limit": 1}],
    "result_format": "json", "result_type": "full",
}
s.viz_type = "big_number_total"
s.params = json.dumps(params_bn)
s.query_context = json.dumps(qc)
db.session.commit()

r = requests.get(f'{SUPERSET}/api/v1/chart/145/data/', headers=headers, params={'force': 'true'})
print(f"  API: {r.status_code}, data exists: {bool(r.json().get('result'))}")

# Test 2: big_number
print("\n=== Test 2: big_number ===")
params_bn2 = {
    "viz_type": "big_number",
    "metric": metric,
    "granularity_sqla": "angkatan",
    "time_grain_sqla": "P1Y",
    "header_font_size": 0.4,
    "subheader_font_size": 0.0,
    "y_axis_format": ",.0f",
}
qc2 = {
    "datasource": {"id": 27, "type": "table"},
    "queries": [{"metrics": [metric], "columns": ["angkatan"], "row_limit": 100, "orderby": [["angkatan", True]]}],
    "result_format": "json", "result_type": "full",
}
s.viz_type = "big_number"
s.params = json.dumps(params_bn2)
s.query_context = json.dumps(qc2)
db.session.commit()

r = requests.get(f'{SUPERSET}/api/v1/chart/145/data/', headers=headers, params={'force': 'true'})
print(f"  API: {r.status_code}, rows: {len(r.json().get('result', [{}])[0].get('data', []))}")

# Test 3: table
print("\n=== Test 3: table ===")
params_tbl = {
    "viz_type": "table",
    "all_columns": [],
    "metrics": [metric],
    "row_limit": 1,
}
s.viz_type = "table"
s.params = json.dumps(params_tbl)
s.query_context = json.dumps(qc)
db.session.commit()

r = requests.get(f'{SUPERSET}/api/v1/chart/145/data/', headers=headers, params={'force': 'true'})
data = r.json()
result = data.get('result', [{}])[0] if data.get('result') else {}
print(f"  API: {r.status_code}, data: {result.get('data', [])}")

# Test 4: pie (single value as pie)
print("\n=== Test 4: pie ===")
params_pie = {
    "viz_type": "pie",
    "groupby": [],
    "metric": metric,
    "row_limit": 1,
}
qc_pie = {
    "datasource": {"id": 27, "type": "table"},
    "queries": [{"metrics": [metric], "row_limit": 1}],
    "result_format": "json", "result_type": "full",
}
s.viz_type = "pie"
s.params = json.dumps(params_pie)
s.query_context = json.dumps(qc_pie)
db.session.commit()

r = requests.get(f'{SUPERSET}/api/v1/chart/145/data/', headers=headers, params={'force': 'true'})
print(f"  API: {r.status_code}, data: {r.json().get('result', [{}])[0].get('data', []) if r.json().get('result') else 'none'}")

# Restore
s.viz_type = orig_viz
s.params = orig_params
s.query_context = orig_qc
db.session.commit()
print("\nRestored original chart 145")
