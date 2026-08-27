"""
Check if chart 76 is in layout
"""
import requests, json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s

s = api()

r = s.get(f"{BASE}/api/v1/dashboard/3")
pos = json.loads(r.json()["result"].get("position_json", "{}"))

chart_ids = []
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        cid = val.get("meta", {}).get("chartId")
        if cid:
            chart_ids.append(cid)

print(f"Charts in layout: {len(chart_ids)}")
print(f"Chart IDs: {sorted(chart_ids)}")
print(f"\nChart 76 in layout: {76 in chart_ids}")
