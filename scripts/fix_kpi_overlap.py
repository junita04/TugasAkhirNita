"""
FIX 8 KPI: Set header_font_size to small value so big number has space.
header_font_size controls the HEADER text, not the big number.
Big number auto-sizes to fill remaining space.
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

# Fix 8 KPI: small header, big number auto-sizes to fill space
# header_font_size=0.2 means header is 20% of max, leaving 80% for big number
kpi_ids = [145, 146, 147, 148, 149, 150, 151, 152]
for cid in kpi_ids:
    s = db.session.query(Slice).get(cid)
    if not s:
        continue
    params = json.loads(s.params) if s.params else {}
    params['header_font_size'] = 0.2
    params['subheader_font_size'] = 0.15
    s.params = json.dumps(params)
    print(f"  ID={cid:3d} {s.slice_name:35s} header=0.2 sub=0.15")
db.session.commit()

# Validate
print("\nValidation:")
for cid in kpi_ids:
    r = requests.get(f'{SUPERSET}/api/v1/chart/{cid}/data/', headers=headers, params={'force': 'true'})
    s = db.session.query(Slice).get(cid)
    params = json.loads(s.params) if s.params else {}
    status = "PASS" if r.status_code == 200 else f"FAIL({r.status_code})"
    print(f"  ID={cid:3d} {s.slice_name:35s} hfs={params.get('header_font_size')} {status}")

print(f"\nURL: http://localhost:8088/superset/dashboard/6/")
