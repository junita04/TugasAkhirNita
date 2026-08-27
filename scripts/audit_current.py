import requests, json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    r0 = s.get(f"{BASE}/api/v1/security/csrf_token/")
    s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": BASE})
    return s

s = api()

# Check confusion matrix (chart 85)
print("=== CHART 85: Confusion Matrix ===")
r = s.get(f"{BASE}/api/v1/chart/85")
if r.status_code == 200:
    c = r.json()["result"]
    print(f"viz_type: {c['viz_type']}")
    print(f"datasource_id: {c['datasource_id']}")
    params = json.loads(c["params"])
    print(f"params: {json.dumps(params, indent=2)}")
    qc_str = c.get("query_context")
    if qc_str:
        qc = json.loads(qc_str)
        print(f"QC queries: {json.dumps(qc['queries'], indent=2)}")
else:
    print(f"NOT FOUND: {r.status_code}")

# Check chart 100 (Distribusi IPK)
print("\n=== CHART 100: Distribusi IPK ===")
r = s.get(f"{BASE}/api/v1/chart/100")
if r.status_code == 200:
    c = r.json()["result"]
    print(f"viz_type: {c['viz_type']}")
    print(f"datasource_id: {c['datasource_id']}")
    params = json.loads(c["params"])
    print(f"params: {json.dumps(params, indent=2)}")
    qc_str = c.get("query_context")
    if qc_str:
        qc = json.loads(qc_str)
        print(f"QC queries: {json.dumps(qc['queries'], indent=2)}")
        # Test
        r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
        print(f"API test: {r2.status_code}")
        if r2.status_code == 200:
            data = r2.json()
            if "result" in data and data["result"]:
                rc = data["result"][0].get("rowcount", "?")
                print(f"  rowcount: {rc}")
else:
    print(f"NOT FOUND: {r.status_code}")

# Also check what datasets are available
print("\n=== DATASETS ===")
for ds_id in [5, 6, 7, 8, 9, 10]:
    r = s.get(f"{BASE}/api/v1/dataset/{ds_id}")
    if r.status_code == 200:
        ds = r.json()["result"]
        cols = [c["column_name"] for c in ds.get("columns", [])]
        print(f"Dataset {ds_id} ({ds['table_name']}): {cols}")
