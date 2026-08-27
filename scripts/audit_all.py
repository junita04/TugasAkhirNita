import requests, json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    return s

s = api()

# Get dashboard position_json
r = s.get(f"{BASE}/api/v1/dashboard/3")
dash = r.json()["result"]
pos = json.loads(dash.get("position_json", "{}"))

chart_refs = []
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        chart_id = meta.get("chartId")
        if chart_id:
            chart_refs.append(chart_id)

print(f"Charts in layout: {len(chart_refs)}")
print()

ok = 0
fail = 0
errors = []

for cid in sorted(chart_refs):
    r1 = s.get(f"{BASE}/api/v1/chart/{cid}")
    if r1.status_code != 200:
        print(f"Chart {cid:4d}: NOT FOUND")
        fail += 1
        errors.append(f"Chart {cid}: NOT FOUND")
        continue

    c = r1.json()["result"]
    name = c["slice_name"]
    viz = c["viz_type"]
    ds_id = c["datasource_id"]
    qc_str = c.get("query_context")

    if not qc_str:
        print(f"Chart {cid:4d}: {viz:25s} | {name:45s} | NO QUERY_CONTEXT")
        fail += 1
        errors.append(f"Chart {cid}: NO QUERY_CONTEXT")
        continue

    qc = json.loads(qc_str)
    r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)

    if r2.status_code == 200:
        data = r2.json()
        if "result" in data and data["result"]:
            rc = data["result"][0].get("rowcount", "?")
            print(f"Chart {cid:4d}: OK | {rc:>5} rows | {viz:25s} | {name}")
            ok += 1
        else:
            print(f"Chart {cid:4d}: OK |     0 rows | {viz:25s} | {name}")
            ok += 1
    else:
        try:
            err = r2.json().get("message", "")[:60]
        except:
            err = r2.text[:60]
        print(f"Chart {cid:4d}: FAIL | {viz:25s} | {name} | {err}")
        fail += 1
        errors.append(f"Chart {cid}: {err}")

print()
print(f"TOTAL:   {len(chart_refs)}")
print(f"VALID:   {ok}")
print(f"BROKEN:  {fail}")
if errors:
    print("ERRORS:")
    for e in errors:
        print(f"  - {e}")
