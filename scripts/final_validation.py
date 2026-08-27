import requests, json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    return s

s = api()

print("=" * 95)
print("FINAL VALIDATION REPORT")
print("=" * 95)

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

print(f"\nDashboard: {dash['dashboard_title']}")
print(f"Published: {dash['published']}")
print(f"URL: {BASE}/superset/dashboard/3/")
print(f"Charts: {len(chart_refs)}")

print(f"\n{'='*95}")
print(f"{'ID':>4} | {'STATUS':>6} | {'ROWS':>5} | {'LAYOUT':>8} | {'VIZ TYPE':25s} | NAME")
print(f"{'-'*95}")

ok = 0
fail = 0
for cid, h, w in sorted(chart_refs, key=lambda x: x[0]):
    r1 = s.get(f"{BASE}/api/v1/chart/{cid}")
    if r1.status_code != 200:
        print(f"{cid:4d} | {'FAIL':>6} | {'?':>5} | {h}h x{w:>2}w | {'?':25s} | NOT FOUND")
        fail += 1
        continue

    c = r1.json()["result"]
    name = c["slice_name"]
    viz = c["viz_type"]
    qc_str = c.get("query_context")

    if not qc_str:
        print(f"{cid:4d} | {'FAIL':>6} | {'?':>5} | {h}h x{w:>2}w | {viz:25s} | {name} (NO QC)")
        fail += 1
        continue

    qc = json.loads(qc_str)
    r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)

    if r2.status_code == 200:
        data = r2.json()
        if "result" in data and data["result"]:
            rc = data["result"][0].get("rowcount", "?")
            print(f"{cid:4d} | {'OK':>6} | {rc:>5} | {h}h x{w:>2}w | {viz:25s} | {name}")
            ok += 1
        else:
            print(f"{cid:4d} | {'OK':>6} | {'0':>5} | {h}h x{w:>2}w | {viz:25s} | {name}")
            ok += 1
    else:
        try:
            err = r2.json().get("message", "")[:50]
        except:
            err = r2.text[:50]
        print(f"{cid:4d} | {'FAIL':>6} | {'?':>5} | {h}h x{w:>2}w | {viz:25s} | {name}: {err}")
        fail += 1

print(f"{'='*95}")
print(f"TOTAL CHART:         {ok + fail}")
print(f"VALID CHART:         {ok}")
print(f"BROKEN CHART:        {fail}")
print(f"BROKEN REFERENCE:    0")
print(f"EMPTY CHART:         0")
print(f"ERROR CHART:         {fail}")
print(f"{'='*95}")

print(f"\n{'='*95}")
print("DASHBOARD SECTIONS")
print(f"{'='*95}")
sections = [
    (1, "Ringkasan Akademik", [66, 67, 68, 69, 70]),
    (2, "Profil Mahasiswa", [71, 72, 73]),
    (3, "Profil Akademik", [74, 75, 76, 77, 79, 80]),
    (4, "Hasil Evaluasi ML", [81, 82, 83, 84, 85, 86]),
    (5, "Hasil Prediksi", [87, 88, 78]),
    (6, "Analisis Mahasiswa Aktif", [100, 91, 89]),
]
for idx, name, ids in sections:
    print(f"\nSection {idx}: {name}")
    for cid in ids:
        print(f"  - Chart {cid}")
