import requests, json

s = requests.Session()
r = s.post("http://localhost:8088/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
token = r.json()["access_token"]
s.headers.update({"Authorization": "Bearer " + token, "Content-Type": "application/json"})
r0 = s.get("http://localhost:8088/api/v1/security/csrf_token/")
s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": "http://localhost:8088"})

# Audit broken charts
for cid in [68, 69, 70, 72, 73]:
    r = s.get(f"http://localhost:8088/api/v1/chart/{cid}")
    c = r.json()["result"]
    name = c["slice_name"]
    params = json.loads(c["params"])
    qc_str = c.get("query_context")
    qc = json.loads(qc_str) if qc_str else None

    viz = c["viz_type"]
    ds = c["datasource_id"]
    print(f"=== Chart {cid}: {name} ===")
    print(f"  viz_type: {viz}")
    print(f"  datasource_id: {ds}")
    print(f"  params: {json.dumps(params, indent=4)}")
    if qc:
        q = qc["queries"][0] if qc.get("queries") else {}
        print(f"  QC metrics: {q.get('metrics', [])}")
        print(f"  QC columns: {q.get('columns', [])}")
        print(f"  QC filters: {q.get('filters', [])}")
    else:
        print(f"  QC: None")

    if qc:
        r2 = s.post("http://localhost:8088/api/v1/chart/data", json=qc)
        if r2.status_code == 200:
            data = r2.json()
            if "result" in data and data["result"]:
                for res in data["result"]:
                    rc = res.get("rowcount", "?")
                    print(f"  DATA: rowcount={rc}")
                    if res.get("data"):
                        for row in res["data"][:5]:
                            print(f"    {row}")
        else:
            print(f"  QUERY FAILED: {r2.status_code} {r2.text[:200]}")
    print()
