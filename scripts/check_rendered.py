"""
Debug: Check the actual rendered HTML of big_number_total to understand font sizes.
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

# Get chart data for 145 with different header_font_size values
# Test with current (0.2) and with 0.0 (no header)
for hfs in [0.0, 0.1, 0.2, 0.3, 0.4]:
    s = db.session.query(Slice).get(145)
    params = json.loads(s.params) if s.params else {}
    params['header_font_size'] = hfs
    s.params = json.dumps(params)
    db.session.commit()
    
    r = requests.get(f'{SUPERSET}/api/v1/chart/145/data/', headers=headers, params={'force': 'true'})
    status = "PASS" if r.status_code == 200 else f"FAIL({r.status_code})"
    print(f"  header_font_size={hfs}: {status}")

# Also check what the chart rendering endpoint looks like
# Try getting the chart HTML
r = requests.get(f'{SUPERSET}/api/v1/chart/145/', headers=headers)
if r.status_code == 200:
    chart_data = r.json().get('result', {})
    print(f"\nChart 145 info:")
    print(f"  viz_type: {chart_data.get('viz_type')}")
    print(f"  params: {chart_data.get('params')}")
