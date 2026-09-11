"""
Test: Try header_font_size=0.6 with subheader=0.0
The header_font_size IS the big number font size.
0.4 was too small. Try 0.6.
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

# Fix only chart 145 (Total Mahasiswa) first
s = db.session.query(Slice).get(145)
if s:
    params = json.loads(s.params) if s.params else {}
    print(f"Before: {json.dumps(params)}")
    
    params['header_font_size'] = 0.6
    params['subheader_font_size'] = 0.0
    s.params = json.dumps(params)
    db.session.commit()
    
    print(f"After: {json.dumps(params)}")
    
    # Test API
    r = requests.get(f'{SUPERSET}/api/v1/chart/145/data/', headers=headers, params={'force': 'true'})
    if r.status_code == 200:
        data = r.json()
        if 'result' in data and data['result']:
            row = data['result'][0].get('data', [{}])
            val = list(row[0].values())[0] if row else '?'
            print(f"API: PASS, value={val}")
        else:
            print("API: FAIL, empty result")
    else:
        print(f"API: FAIL, HTTP {r.status_code}")

print(f"\nURL: http://localhost:8088/superset/dashboard/6/")
print("Check if the number is now larger.")
