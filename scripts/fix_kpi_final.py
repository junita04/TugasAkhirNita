"""
FIX KPI: header_font_size IS the big number font size.
Setting it to 0.0 hides the value. 
Need reasonable value like 0.4 for big number to show.
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

# First, check what params big_number_total actually reads
# by testing with different values
print("=== Testing big_number_total params ===")

# Test: what happens with header_font_size=0.4 (default)?
s = db.session.query(Slice).get(145)
params = json.loads(s.params) if s.params else {}
print(f"Current params: {json.dumps(params)}")

# The problem: header_font_size=0.0 hides the value
# The fix: use a reasonable value for the big number
# subheader_font_size controls the subtitle text

# Set header_font_size to 0.4 (reasonable big number size)
# Set subheader_font_size to 0 (no subtitle needed)
kpi_ids = [145, 146, 147, 148, 149, 150, 151, 152]
for cid in kpi_ids:
    s = db.session.query(Slice).get(cid)
    if not s:
        continue
    params = json.loads(s.params) if s.params else {}
    # header_font_size = big number font size (0.4 is default/reasonable)
    # subheader_font_size = subtitle (0 to hide)
    params['header_font_size'] = 0.4
    params['subheader_font_size'] = 0.0
    s.params = json.dumps(params)
    print(f"  ID={cid:3d} {s.slice_name:35s} header=0.4 sub=0.0")
db.session.commit()

# Validate
print("\n=== Validation ===")
for cid in kpi_ids:
    r = requests.get(f'{SUPERSET}/api/v1/chart/{cid}/data/', headers=headers, params={'force': 'true'})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if 'result' in data and data['result']:
            row = data['result'][0].get('data', [{}])
            val = list(row[0].values())[0] if row else '?'
            print(f"  PASS  ID={cid:3d} {s.slice_name:35s} value={val}")
        else:
            print(f"  FAIL  ID={cid:3d} {s.slice_name} empty")
    else:
        print(f"  FAIL  ID={cid:3d} {s.slice_name} HTTP {r.status_code}")

print(f"\nURL: http://localhost:8088/superset/dashboard/6/")
