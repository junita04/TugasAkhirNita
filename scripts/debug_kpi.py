"""
Debug: Check exactly how big_number_total renders and what controls value size.
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

# Check current config for chart 145
s = db.session.query(Slice).get(145)
params = json.loads(s.params) if s.params else {}
print(f"Chart 145 current params: {json.dumps(params, indent=2)}")

# Check what other charts use for reference
# Look at Dashboard 5's big_number charts
for cid in [145, 146, 147, 148, 149, 150, 151, 152]:
    s = db.session.query(Slice).get(cid)
    if s:
        params = json.loads(s.params) if s.params else {}
        print(f"ID={cid:3d} viz={s.viz_type:25s} hfs={params.get('header_font_size','?')} sfs={params.get('subheader_font_size','?')} fmt={params.get('y_axis_format','?')}")

# Now check: what does big_number_total actually support?
# Let me look at the Superset source
print("\n--- Checking big_number_total source ---")
import subprocess
result = subprocess.run(
    ['find', '/app', '-name', '*.py', '-path', '*/plugins/*'],
    capture_output=True, text=True
)
plugin_files = [f for f in result.stdout.strip().split('\n') if f]
print(f"Plugin files found: {len(plugin_files)}")

# Check if there's a BigNumberTotal plugin
for f in plugin_files:
    if 'big_number' in f.lower() or 'bignumber' in f.lower():
        print(f"  Found: {f}")
