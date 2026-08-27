"""
Fix KPI widths back to full width
"""
import requests, json

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

kpi_widths = {66: 3, 67: 3, 68: 2, 69: 2, 70: 2}

for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        chart_id = meta.get("chartId")
        if chart_id in kpi_widths:
            meta["width"] = kpi_widths[chart_id]

r = s.put(f"{BASE}/api/v1/dashboard/3", json={"position_json": json.dumps(pos)})
print(f"Updated: {r.status_code}")

# Verify
r2 = s.get(f"{BASE}/api/v1/dashboard/3")
pos2 = json.loads(r2.json()["result"]["position_json"])
total = 0
for key, val in pos2.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        cid = meta.get("chartId")
        if cid in kpi_widths:
            w = meta.get("width")
            total += w
            print(f"  Chart {cid}: {w}w | {meta.get('sliceName')}")
print(f"Total: {total}/12")
