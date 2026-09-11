"""
Validate all 28 dashboard charts + 5 prediction KPIs (163-167).
"""
import sys, requests
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

# Dashboard 6 charts: KPIs 145-152, Prediction KPIs 163-167, Charts 153-162
all_charts = list(range(145, 153)) + list(range(153, 163)) + list(range(163, 168))

print("=== All Dashboard 6 Charts ===")
pass_count = 0
fail_count = 0

for cid in sorted(set(all_charts)):
    r = requests.get(f'{SUPERSET}/api/v1/chart/{cid}/data/', headers=headers, params={'force': 'true'})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if 'result' in data and data['result']:
            q = data['result'][0]
            status = q.get('status', 'unknown')
            if status == 'success':
                pass_count += 1
                print(f"  PASS  ID={cid:3d} {s.slice_name[:40]:40s} {s.viz_type[:25]}")
            else:
                fail_count += 1
                print(f"  WARN  ID={cid:3d} {s.slice_name[:40]:40s} {s.viz_type[:25]} status={status}")
        else:
            fail_count += 1
            print(f"  FAIL  ID={cid:3d} {s.slice_name[:40]:40s} empty result")
    else:
        fail_count += 1
        err = r.text[:80] if r.text else ""
        print(f"  FAIL  ID={cid:3d} {s.slice_name[:40]:40s} HTTP {r.status_code} {err}")

print(f"\n=== RESULT: {pass_count} PASS, {fail_count} FAIL ===")
print(f"URL: http://localhost:8088/superset/dashboard/6/")
