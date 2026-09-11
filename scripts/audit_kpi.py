"""
Audit current state of KPI charts 145-152.
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

for cid in range(145, 153):
    s = db.session.query(Slice).get(cid)
    if not s:
        print(f'ID={cid}: NOT FOUND')
        continue
    p = json.loads(s.params) if s.params else {}
    qc = json.loads(s.query_context) if s.query_context else {}
    print(f'--- ID={cid} ---')
    print(f'  name: {s.slice_name}')
    print(f'  viz_type: {s.viz_type}')
    print(f'  datasource_id: {s.datasource_id}')
    print(f'  datasource_type: {s.datasource_type}')
    vt = p.get("viz_type", "MISSING")
    mt = p.get("metrics", "MISSING")
    ac = p.get("all_columns", "N/A")
    hfs = p.get("header_font_size", "N/A")
    sfs = p.get("subheader_font_size", "N/A")
    print(f'  params viz_type: {vt}')
    print(f'  params metrics: {mt}')
    print(f'  params all_columns: {ac}')
    print(f'  params header_font_size: {hfs}')
    print(f'  params subheader_font_size: {sfs}')
    qds = qc.get("datasource", "MISSING")
    qqs = qc.get("queries", "MISSING")
    print(f'  query_context datasource: {qds}')
    print(f'  query_context queries: {qqs}')
    print()
