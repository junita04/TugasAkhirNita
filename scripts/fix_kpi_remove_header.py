"""
FIX: Set header_font_size=0.0 to remove internal header.
Big number gets 100% of space. Chart title serves as label.
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

# Fix 8 KPI: remove internal header, let big number fill entire space
kpi_ids = [145, 146, 147, 148, 149, 150, 151, 152]
for cid in kpi_ids:
    s = db.session.query(Slice).get(cid)
    if not s:
        continue
    params = json.loads(s.params) if s.params else {}
    # Remove internal header - the chart title from dashboard layout is the label
    params['header_font_size'] = 0.0
    params['subheader_font_size'] = 0.0
    s.params = json.dumps(params)
    print(f"  ID={cid:3d} {s.slice_name:35s} header=0.0 (removed)")
db.session.commit()

# Validate
print("\nValidation:")
for cid in kpi_ids:
    r = requests.get(f'{SUPERSET}/api/v1/chart/{cid}/data/', headers=headers, params={'force': 'true'})
    s = db.session.query(Slice).get(cid)
    status = "PASS" if r.status_code == 200 else f"FAIL({r.status_code})"
    print(f"  ID={cid:3d} {s.slice_name:35s} {status}")

print(f"\nURL: http://localhost:8088/superset/dashboard/6/")
print("Note: Chart titles serve as labels. Big number fills entire card.")
