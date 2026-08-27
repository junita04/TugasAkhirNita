import requests, json

s = requests.Session()
r = s.post("http://localhost:8088/api/v1/security/login", json={"username": "admin", "password": "change-me", "provider": "db"})
token = r.json()["access_token"]
s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
r0 = s.get("http://localhost:8088/api/v1/security/csrf_token/")
s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": "http://localhost:8088"})

ok = 0
fail = 0
for cid in range(1, 27):
    r = s.get(f"http://localhost:8088/api/v1/chart/{cid}")
    if r.status_code != 200:
        print(f"  Chart {cid:2d}: NOT FOUND")
        fail += 1
        continue
    c = r.json()["result"]
    name = c["slice_name"]
    qc_str = c.get("query_context")
    if not qc_str:
        print(f"  Chart {cid:2d}: NO QC - {name}")
        fail += 1
        continue
    qc = json.loads(qc_str)
    r2 = s.post("http://localhost:8088/api/v1/chart/data", json=qc)
    if r2.status_code == 200:
        data = r2.json()
        if "result" in data and data["result"]:
            rc = data["result"][0].get("rowcount", "?")
            print(f"  Chart {cid:2d}: OK ({rc} rows) - {name}")
            ok += 1
        else:
            print(f"  Chart {cid:2d}: OK (empty) - {name}")
            ok += 1
    else:
        try:
            err = r2.json().get("message", "")[:60]
        except:
            err = r2.text[:60]
        print(f"  Chart {cid:2d}: FAIL ({r2.status_code}) - {name}: {err}")
        fail += 1

print(f"\nRESULT: {ok}/{ok+fail} charts render data correctly")
print(f"Dashboard URL: http://localhost:8088/superset/dashboard/3/")
