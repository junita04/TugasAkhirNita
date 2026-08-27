"""
Fix KPI layout: 5 KPIs filling full width (12 columns)
Use width distribution: 3+3+2+2+2 = 12
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

# Get current dashboard
r = s.get(f"{BASE}/api/v1/dashboard/3")
pos = json.loads(r.json()["result"]["position_json"])

# Fix KPI widths: 3+3+2+2+2 = 12 (full width)
kpi_widths = {
    66: 3,  # Total Mahasiswa
    67: 3,  # Mahasiswa Aktif
    68: 2,  # Mahasiswa Lulus
    69: 2,  # Tepat Waktu
    70: 2,  # Terlambat
}

for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        chart_id = meta.get("chartId")
        if chart_id in kpi_widths:
            old_w = meta.get("width")
            new_w = kpi_widths[chart_id]
            meta["width"] = new_w
            print(f"Chart {chart_id}: {old_w}w -> {new_w}w ({meta.get('sliceName')})")

# Update dashboard
r = s.put(f"{BASE}/api/v1/dashboard/3", json={"position_json": json.dumps(pos)})
print(f"\nDashboard updated: {r.status_code}")

# Verify
r2 = s.get(f"{BASE}/api/v1/dashboard/3")
pos2 = json.loads(r2.json()["result"]["position_json"])
total_width = 0
for key, val in pos2.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        chart_id = meta.get("chartId")
        if chart_id in kpi_widths:
            w = meta.get("width")
            total_width += w
            print(f"  Chart {chart_id}: {w}w | {meta.get('sliceName')}")

print(f"\nTotal KPI width: {total_width}/12 columns")
print(f"Full width: {'YES' if total_width == 12 else 'NO'}")
