"""
Apply header_font_size=0.6 to all 8 KPI.
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

kpi_ids = [145, 146, 147, 148, 149, 150, 151, 152]
for cid in kpi_ids:
    s = db.session.query(Slice).get(cid)
    if not s:
        continue
    params = json.loads(s.params) if s.params else {}
    params['header_font_size'] = 0.6
    params['subheader_font_size'] = 0.0
    s.params = json.dumps(params)
    print(f"  ID={cid:3d} {s.slice_name:35s} header=0.6")
db.session.commit()

# Validate
print("\nValidation:")
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
