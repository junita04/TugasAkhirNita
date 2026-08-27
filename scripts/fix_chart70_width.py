"""
Fix chart 70 width from 12 to 3
"""
import requests
import json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r0 = s.get(f"{BASE}/api/v1/security/csrf_token/")
    s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": BASE})
    return s

s = api()

r = s.get(f"{BASE}/api/v1/dashboard/3")
pos = json.loads(r.json()["result"]["position_json"])

# Fix chart 70 width
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        if meta.get("chartId") == 70:
            meta["width"] = 3
            print(f"Fixed chart 70: {meta.get('height')}h x {meta.get('width')}w")

r2 = s.put(f"{BASE}/api/v1/dashboard/3", json={"position_json": json.dumps(pos)})
print(f"Updated: {r2.status_code}")

# Verify all widths
r3 = s.get(f"{BASE}/api/v1/dashboard/3")
pos2 = json.loads(r3.json()["result"]["position_json"])
for key, val in pos2.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        print(f"  Chart {meta.get('chartId')}: {meta.get('height')}h x {meta.get('width')}w | {meta.get('sliceName')}")
