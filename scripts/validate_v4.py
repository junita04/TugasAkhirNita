"""
FINAL VALIDATION - 25 charts, 8 sections
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

chart_refs = []
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        chart_id = meta.get("chartId")
        height = meta.get("height", "?")
        width = meta.get("width", "?")
        if chart_id:
            chart_refs.append((chart_id, height, width))

print("=" * 110)
print("FINAL DASHBOARD VALIDATION - 25 CHARTS, 8 SECTIONS")
print("=" * 110)
print(f"\nDashboard: {dash['dashboard_title']}")
print(f"URL: {BASE}/superset/dashboard/3/")
print(f"Charts: {len(chart_refs)}")

sections = {
    1: "Ringkasan Akademik",
    2: "Profil Mahasiswa",
    3: "Performa Akademik",
    4: "Status Kelulusan Aktual",
    5: "Hasil Prediksi Mahasiswa Aktif",
    6: "Analisis Mahasiswa Aktif",
    7: "Confusion Matrix",
    8: "Hasil Evaluasi Model Machine Learning",
}
print()
for idx, name in sections.items():
    print(f"  Section {idx}: {name}")

print(f"\n{'='*110}")
print(f"{'ID':>4} | {'STATUS':>6} | {'ROWS':>5} | {'LAYOUT':>8} | {'VIZ TYPE':25s} | NAME")
print(f"{'-'*110}")

ok = 0
for cid, h, w in sorted(chart_refs, key=lambda x: x[0]):
    r1 = s.get(f"{BASE}/api/v1/chart/{cid}")
    c = r1.json()["result"]
    name = c["slice_name"]
    viz = c["viz_type"]
    qc_str = c.get("query_context")
    qc = json.loads(qc_str) if qc_str else None
    r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc) if qc else None
    if r2 and r2.status_code == 200:
        data = r2.json()
        rc = data["result"][0].get("rowcount", "?") if data.get("result") else 0
        print(f"{cid:4d} | {'OK':>6} | {rc:>5} | {h}h x{w:>2}w | {viz:25s} | {name}")
        ok += 1
    else:
        print(f"{cid:4d} | {'FAIL':>6} | {'?':>5} | {h}h x{w:>2}w | {viz:25s} | {name}")

print(f"{'='*110}")
print(f"VALID: {ok}/{len(chart_refs)}")

# Verify chart 87 is stacked
r3 = s.get(f"{BASE}/api/v1/chart/87")
c87 = r3.json()["result"]
p87 = json.loads(c87.get("params", "{}"))
print(f"\nChart 87 stacked: {p87.get('stack')}")
