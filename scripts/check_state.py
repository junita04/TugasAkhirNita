"""
Check current dashboard state
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
dash = r.json()["result"]
pos = json.loads(dash.get("position_json", "{}"))

chart_ids = []
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        cid = val.get("meta", {}).get("chartId")
        if cid:
            chart_ids.append(cid)

print(f"Charts in layout: {len(chart_ids)}")
print(f"Chart IDs: {sorted(chart_ids)}")

# Check if ML KPI cards exist in layout
ml_kpis = [81, 82, 83, 84]
for ml in ml_kpis:
    if ml in chart_ids:
        print(f"  WARNING: ML KPI {ml} is STILL in layout!")
    else:
        print(f"  ML KPI {ml}: NOT in layout (already removed)")
