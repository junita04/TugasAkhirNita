"""
DIAGNOSE: Check why 8 KPI charts have warning icons.
Test one chart at a time.
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

# Check chart 145 (Total Mahasiswa) in detail
s = db.session.query(Slice).get(145)
if s:
    params = json.loads(s.params) if s.params else {}
    qc = json.loads(s.query_context) if s.query_context else None
    
    print(f"=== Chart 145: {s.slice_name} ===")
    print(f"viz_type: {s.viz_type}")
    print(f"datasource_id: {s.datasource_id}")
    print(f"datasource_type: {s.datasource_type}")
    print(f"params: {json.dumps(params, indent=2)}")
    print(f"query_context: {json.dumps(qc, indent=2) if qc else 'None'}")
    
    # Test API
    r = requests.get(f'{SUPERSET}/api/v1/chart/145/data/', headers=headers, params={'force': 'true'})
    print(f"\nAPI Status: {r.status_code}")
    if r.status_code != 200:
        print(f"Error: {r.text[:500]}")
    else:
        data = r.json()
        if 'result' in data and data['result']:
            for q in data['result']:
                print(f"  rowcount: {q.get('rowcount')}")
                print(f"  colnames: {q.get('colnames')}")
                print(f"  data: {q.get('data', [])[:3]}")
                print(f"  error: {q.get('error')}")
                print(f"  status: {q.get('status')}")
        else:
            print(f"  No result data")
            print(f"  Full response: {json.dumps(data, indent=2)[:500]}")
