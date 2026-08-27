"""
FINAL VALIDATION - 20 charts
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

print("=" * 105)
print("FINAL DASHBOARD VALIDATION - 20 CHARTS")
print("=" * 105)
print(f"\nDashboard: {dash['dashboard_title']}")
print(f"URL: {BASE}/superset/dashboard/3/")
print(f"Charts: {len(chart_refs)}")

sections = {
    1: "Ringkasan Akademik",
    2: "Profil Mahasiswa",
    3: "Performa Akademik",
    4: "Hasil Evaluasi Model",
    5: "Hasil Prediksi Mahasiswa Aktif",
}
print()
for idx, name in sections.items():
    print(f"  Section {idx}: {name}")

print(f"\n{'='*105}")
print(f"{'ID':>4} | {'STATUS':>6} | {'ROWS':>5} | {'LAYOUT':>8} | {'VIZ TYPE':25s} | NAME")
print(f"{'-'*105}")

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

print(f"{'='*105}")
print(f"VALID: {ok}/{len(chart_refs)}")

# Check ML KPIs not in layout
ml_kpis = [81, 82, 83, 84]
for ml in ml_kpis:
    if ml in [cid for cid, _, _ in chart_refs]:
        print(f"  WARNING: ML KPI {ml} is STILL in layout!")
    else:
        print(f"  ML KPI {ml}: NOT in layout")
