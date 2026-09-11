"""
RESTORE KPI 145 (Total Mahasiswa) to big_number_total.
Last working config: datasource=27, big_number_total, SQL metric, hfs=0.6, sfs=0.0
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

# Restore chart 145 to big_number_total on dim_mahasiswa
s = db.session.query(Slice).get(145)
if not s:
    print("ERROR: chart 145 not found")
    exit(1)

metric = {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total Mahasiswa"}

params = {
    "viz_type": "big_number_total",
    "metric": metric,
    "header_font_size": 0.6,
    "subheader_font_size": 0.0,
    "y_axis_format": "SMART_NUMBER",
    "time_grain_sqla": "P1D",
    "header_color": "",
    "subheader_color": "",
}

qc = {
    "datasource": {"id": 27, "type": "table"},
    "queries": [{
        "metrics": [metric],
        "row_limit": 1,
    }],
    "result_format": "json",
    "result_type": "full",
}

s.viz_type = "big_number_total"
s.datasource_id = 27
s.datasource_type = "table"
s.params = json.dumps(params)
s.query_context = json.dumps(qc)

db.session.commit()

# Validate via API
print("Validating chart 145...")
r = requests.get(f'{SUPERSET}/api/v1/chart/145/data/', headers=headers, params={'force': 'true'})
if r.status_code == 200:
    data = r.json()
    if 'result' in data and data['result']:
        q = data['result'][0]
        d = q.get('data', [])
        cols = q.get('colnames', [])
        print(f"  API OK: cols={cols} data={d[:2]} status={q.get('status')}")
    else:
        print("  API: empty result")
else:
    print(f"  API FAIL: HTTP {r.status_code}")
    print(f"  {r.text[:200]}")

# Also check the chart config
p = json.loads(s.params)
print(f"\n  viz_type: {s.viz_type}")
print(f"  datasource_id: {s.datasource_id}")
print(f"  metric: {p.get('metric')}")
print(f"  header_font_size: {p.get('header_font_size')}")
print(f"  subheader_font_size: {p.get('subheader_font_size')}")
print(f"\nURL: http://localhost:8088/superset/dashboard/6/")
