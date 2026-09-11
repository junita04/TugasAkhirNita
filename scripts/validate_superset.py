"""
Validate Superset datasets still work after data update.
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

# Dashboard 6 KPI charts (145-152)
print("=== Dashboard 6 KPI Charts ===")
for cid in range(145, 153):
    r = requests.get(f'{SUPERSET}/api/v1/chart/{cid}/data/', headers=headers, params={'force': 'true'})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if 'result' in data and data['result']:
            q = data['result'][0]
            d = q.get('data', [])
            status = q.get('status', 'unknown')
            val = list(d[0].values())[0] if d else "N/A"
            print(f"  PASS  ID={cid:3d} {s.slice_name:35s} val={val} status={status}")
        else:
            print(f"  FAIL  ID={cid:3d} {s.slice_name} empty")
    else:
        print(f"  FAIL  ID={cid:3d} HTTP {r.status_code}")

# Dashboard 6 prediction KPI charts (163-167)
print("\n=== Dashboard 6 Prediction KPI Charts ===")
for cid in range(163, 168):
    r = requests.get(f'{SUPERSET}/api/v1/chart/{cid}/data/', headers=headers, params={'force': 'true'})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if 'result' in data and data['result']:
            q = data['result'][0]
            d = q.get('data', [])
            status = q.get('status', 'unknown')
            val = list(d[0].values())[0] if d else "N/A"
            print(f"  PASS  ID={cid:3d} {s.slice_name:35s} val={val} status={status}")
        else:
            print(f"  FAIL  ID={cid:3d} {s.slice_name} empty")
    else:
        print(f"  FAIL  ID={cid:3d} HTTP {r.status_code}")

print("\nDone.")
