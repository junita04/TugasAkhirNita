import requests
import json

s = requests.Session()
r = s.post('http://localhost:8088/api/v1/security/login', json={'username':'admin','password':'change-me','provider':'db'})
token = r.json()['access_token']
s.headers.update({'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
r0 = s.get('http://localhost:8088/api/v1/security/csrf_token/')
s.headers.update({'X-CSRFToken': r0.json()['result'], 'Referer': 'http://localhost:8088'})

# Get full dashboard detail with all fields
r = s.get('http://localhost:8088/api/v1/dashboard/1')
d = r.json()['result']

print("=== DASHBOARD DETAIL ===")
for k, v in d.items():
    if k == 'position_json':
        if v:
            pos = json.loads(v) if isinstance(v, str) else v
            chart_refs = {k: v for k, v in pos.items() if isinstance(v, dict) and v.get('type') == 'CHART'}
            print(f"  {k}: {len(pos)} keys, {len(chart_refs)} chart refs")
        else:
            print(f"  {k}: None/empty")
    elif k == 'json_metadata':
        print(f"  {k}: {v}")
    elif k == 'charts':
        print(f"  {k}: {v}")
    elif k == 'slices':
        print(f"  {k}: {v}")
    else:
        val_str = str(v)[:100]
        print(f"  {k}: {val_str}")

# Check the slices endpoint
print("\n=== SLICES CHECK ===")
r2 = s.get('http://localhost:8088/api/v1/dashboard/1/slices')
print(f"  GET /dashboard/1/slices: status={r2.status_code}")
if r2.status_code == 200:
    print(f"  Response: {json.dumps(r2.json())[:500]}")

# Check if there's a PUT endpoint to associate slices
print("\n===尝试关联 charts to dashboard ===")
# The key is that position_json alone is not enough.
# We need to also set the 'slices' relationship.
# Let's try updating the dashboard with the chart IDs.
chart_ids = list(range(1, 27))

# Method 1: Try PUT with json_metadata
update_payload = {
    "json_metadata": json.dumps({
        "chartConfiguration": {},
        "color_scheme": "supersetColors",
        "timed_refresh_immune_slices": [],
        "expanded_slices": {},
        "refresh_frequency": 0,
        "default_filters": "{}",
        "color_scheme_domain": [],
        "label_colors": {},
        "shared_label_colors": {},
        "color_brightness": 0,
        "color_ternary": "",
        "cross_filters_enabled": True,
    }),
}
r3 = s.put('http://localhost:8088/api/v1/dashboard/1', json=update_payload)
print(f"  PUT json_metadata: status={r3.status_code}")

# Method 2: Check if we need to use the older API
# Let's check the Superset version and available endpoints
r4 = s.get('http://localhost:8088/api/v1/info')
print(f"\n=== SUPERSET INFO ===")
try:
    info = r4.json()
    print(f"  {json.dumps(info)[:300]}")
except:
    print(f"  status={r4.status_code}")

# Method 3: Try the legacy endpoint
r5 = s.get('http://localhost:8088/api/v1/dashboard/1', params={"q": "(columns:!(id,dashboard_title,position_json,json_metadata,slices))"})
print(f"\n=== DASHBOARD WITH SLICES ===")
try:
    detail = r5.json()['result']
    print(f"  slices field: {detail.get('slices', 'NOT FOUND')}")
    print(f"  json_metadata: {str(detail.get('json_metadata', 'NONE'))[:300]}")
except Exception as e:
    print(f"  Error: {e}")
