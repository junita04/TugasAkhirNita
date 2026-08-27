import requests, json

s = requests.Session()
r = s.post("http://localhost:8088/api/v1/security/login", json={"username": "admin", "password": "change-me", "provider": "db"})
token = r.json()["access_token"]
s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
r0 = s.get("http://localhost:8088/api/v1/security/csrf_token/")
s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": "http://localhost:8088"})

# Read stored query_context from API and test
for cid in [21, 25]:
    r = s.get(f"http://localhost:8088/api/v1/chart/{cid}")
    c = r.json()["result"]
    qc = json.loads(c.get("query_context", "{}"))
    print(f"Chart {cid} ({c['slice_name']}):")
    print(f"  QC query columns: {qc['queries'][0].get('columns', [])}")
    print(f"  QC query metrics: {qc['queries'][0].get('metrics', [])}")
    print(f"  QC query filters: {qc['queries'][0].get('filters', [])}")
    
    r2 = s.post("http://localhost:8088/api/v1/chart/data", json=qc)
    if r2.status_code == 200:
        data = r2.json()
        if "result" in data and data["result"]:
            rc = data["result"][0].get("rowcount", "?")
            print(f"  Result: OK ({rc} rows)")
        else:
            print(f"  Result: OK (empty)")
    else:
        print(f"  Result: FAILED ({r2.status_code}): {r2.text[:100]}")

# Final count
print("\n--- ALL CHARTS ---")
r = s.get("http://localhost:8088/api/v1/chart/?q=(page_size:100)")
charts = r.json()["result"]
ok = 0
fail = 0
for c in charts:
    cid = c["id"]
    qc = json.loads(c.get("query_context") or "{}")
    if not qc:
        print(f"  Chart {cid:2d}: SKIP (no QC)")
        continue
    r2 = s.post("http://localhost:8088/api/v1/chart/data", json=qc)
    if r2.status_code == 200:
        data = r2.json()
        if "result" in data and data["result"]:
            rc = data["result"][0].get("rowcount", "?")
            print(f"  Chart {cid:2d}: OK ({rc} rows) - {c['slice_name']}")
            ok += 1
        else:
            print(f"  Chart {cid:2d}: OK - {c['slice_name']}")
            ok += 1
    else:
        print(f"  Chart {cid:2d}: FAIL - {c['slice_name']}")
        fail += 1

print(f"\nRESULT: {ok}/{ok+fail} charts working")
