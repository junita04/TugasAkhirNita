import requests, json

s = requests.Session()
r = s.post("http://localhost:8088/api/v1/security/login", json={"username": "admin", "password": "change-me", "provider": "db"})
token = r.json()["access_token"]
s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
r0 = s.get("http://localhost:8088/api/v1/security/csrf_token/")
s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": "http://localhost:8088"})

# Get all chart names
chart_names = {}
for cid in range(1, 27):
    r = s.get(f"http://localhost:8088/api/v1/chart/{cid}")
    if r.status_code == 200:
        chart_names[cid] = r.json()["result"]["slice_name"]

# Get current dashboard position_json
r = s.get("http://localhost:8088/api/v1/dashboard/3")
dash = r.json()["result"]
pos = json.loads(dash["position_json"])

# Update chart names in position_json
updated = 0
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        chart_id = meta.get("chartId")
        if chart_id and chart_id in chart_names:
            old_name = meta.get("sliceName", "")
            new_name = chart_names[chart_id]
            if old_name != new_name:
                meta["sliceName"] = new_name
                updated += 1

print(f"Updated {updated} chart names in position_json")

# Save
r2 = s.put("http://localhost:8088/api/v1/dashboard/3", json={"position_json": json.dumps(pos)})
print(f"Dashboard update: {r2.status_code}")

# Verify dashboard-charts association
r3 = s.get("http://localhost:8088/api/v1/dashboard/3")
dash2 = r3.json()["result"]
print(f"\nDashboard: {dash2['dashboard_title']}")
print(f"Published: {dash2['published']}")
print(f"URL: http://localhost:8088/superset/dashboard/3/")

# Count referenced charts in position_json
pos2 = json.loads(dash2["position_json"])
chart_ids_in_pos = set()
for key, val in pos2.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        cid = val.get("meta", {}).get("chartId")
        if cid:
            chart_ids_in_pos.add(cid)
print(f"Charts referenced in layout: {len(chart_ids_in_pos)}")
