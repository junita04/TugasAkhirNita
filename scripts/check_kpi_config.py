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

# Check current KPI font sizes
print("=== CURRENT KPI CONFIG ===")
for cid in [145, 146, 147, 148, 149, 150, 151, 152, 163, 164, 165, 166, 167]:
    s = db.session.query(Slice).get(cid)
    if s:
        params = json.loads(s.params) if s.params else {}
        hfs = params.get('header_font_size', 'NOT SET')
        sfs = params.get('subheader_font_size', 'NOT SET')
        print(f"  ID={cid:3d} {s.slice_name:35s} header={hfs} sub={sfs}")

# Test chart 156
print("\n=== CHART 156 TEST ===")
r = requests.get(f'{SUPERSET}/api/v1/chart/156/data/', headers=headers, params={'force': 'true'})
print(f"  Status: {r.status_code}")
if r.status_code != 200:
    print(f"  Error: {r.text[:300]}")
else:
    data = r.json()
    if 'result' in data:
        for q in data['result']:
            print(f"  Result keys: {list(q.keys())}")
            if 'data' in q:
                print(f"  Data: {q['data'][:5]}")

# Check what Superset version supports for big_number_total
print("\n=== AVAILABLE VIZ TYPES ===")
from superset.viz import viz_types
for vt in ['big_number', 'big_number_total']:
    if vt in viz_types:
        print(f"  {vt}: AVAILABLE")
        cls = viz_types[vt]
        if hasattr(cls, 'form_fields'):
            for ff in cls.form_fields:
                if 'font' in str(ff).lower() or 'size' in str(ff).lower():
                    print(f"    Font/Size field: {ff}")
    else:
        print(f"  {vt}: NOT FOUND")
