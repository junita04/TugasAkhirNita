"""
Test: Replace Big Number with simple table card.
Table chart is the most stable native viz in Superset.
Single row + single column = card display.
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

# Test: Can we use table chart as a card?
# Create a test table chart for Total Mahasiswa
s145 = db.session.query(Slice).get(145)
if s145:
    # Store original params for rollback
    orig_params = s145.params
    orig_viz = s145.viz_type
    
    # Try table viz
    params = {
        "viz_type": "table",
        "all_columns": [],
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total Mahasiswa"}],
        "row_limit": 1,
        "include_search": False,
        "table_timestamp_format": "smart_date",
        "page_length": 0,
    }
    
    qc = {
        "datasource": {"id": 27, "type": "table"},
        "queries": [{
            "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total Mahasiswa"}],
            "row_limit": 1,
        }],
        "result_format": "json",
        "result_type": "full",
    }
    
    s145.viz_type = "table"
    s145.params = json.dumps(params)
    s145.query_context = json.dumps(qc)
    db.session.commit()
    
    # Test
    r = requests.get(f'{SUPERSET}/api/v1/chart/145/data/', headers=headers, params={'force': 'true'})
    print(f"Table chart test: HTTP {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if 'result' in data and data['result']:
            for q in data['result']:
                print(f"  Data: {q.get('data', [])}")
                print(f"  Colnames: {q.get('colnames', [])}")
    
    # Restore original
    s145.viz_type = orig_viz
    s145.params = orig_params
    db.session.commit()

# Test: big_number (with time axis) vs big_number_total
print("\n--- Testing big_number (not total) ---")
s145 = db.session.query(Slice).get(145)
orig_params = s145.params
orig_viz = s145.viz_type

params_bn = {
    "viz_type": "big_number",
    "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total"},
    "granularity_sqla": "angkatan",
    "time_grain_sqla": "P1Y",
    "header_font_size": 0.4,
    "subheader_font_size": 0.0,
    "y_axis_format": ",.0f",
    "range_bars": False,
}

qc_bn = {
    "datasource": {"id": 27, "type": "table"},
    "queries": [{
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total"}],
        "columns": ["angkatan"],
        "row_limit": 100,
        "orderby": [["angkatan", True]],
    }],
    "result_format": "json",
    "result_type": "full",
}

s145.viz_type = "big_number"
s145.params = json.dumps(params_bn)
s145.query_context = json.dumps(qc_bn)
db.session.commit()

r = requests.get(f'{SUPERSET}/api/v1/chart/145/data/', headers=headers, params={'force': 'true'})
print(f"big_number test: HTTP {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if 'result' in data and data['result']:
        for q in data['result']:
            d = q.get('data', [])
            print(f"  Rows: {len(d)}, Sample: {d[:3]}")

# Restore
s145.viz_type = orig_viz
s145.params = orig_params
db.session.commit()
print("\nRestored original chart 145")
