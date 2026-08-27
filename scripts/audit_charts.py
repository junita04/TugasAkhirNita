"""
Audit chart 100 (IPK Distribution) and related charts
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

# Check chart 100
print("=" * 70)
print("CHART 100: Distribusi IPK Mahasiswa Aktif")
print("=" * 70)
r = s.get(f"{BASE}/api/v1/chart/100")
c = r.json()["result"]
print(f"viz_type: {c['viz_type']}")
print(f"datasource_id: {c['datasource_id']}")
params = json.loads(c["params"]) if c["params"] else {}
print(f"params: {json.dumps(params, indent=2)}")
qc_str = c.get("query_context")
if qc_str:
    qc = json.loads(qc_str)
    print(f"query_context queries: {json.dumps(qc['queries'], indent=2)}")
    # Test the query
    r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
    print(f"API test: {r2.status_code}")
    if r2.status_code == 200:
        data = r2.json()
        if "result" in data and data["result"]:
            rc = data["result"][0].get("rowcount", 0)
            print(f"Row count: {rc}")
        else:
            print("No result data")
    else:
        try:
            print(f"Error: {r2.json()}")
        except:
            print(f"Error: {r2.text[:300]}")
else:
    print("NO query_context!")

# Check chart 89
print("\n" + "=" * 70)
print("CHART 89: Rata-rata Selisih SKS per Semester")
print("=" * 70)
r = s.get(f"{BASE}/api/v1/chart/89")
c = r.json()["result"]
print(f"viz_type: {c['viz_type']}")
params = json.loads(c["params"]) if c["params"] else {}
print(f"params: {json.dumps(params, indent=2)}")
qc_str = c.get("query_context")
if qc_str:
    qc = json.loads(qc_str)
    print(f"query: {json.dumps(qc['queries'], indent=2)}")
    r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
    if r2.status_code == 200:
        data = r2.json()
        if "result" in data and data["result"]:
            d = data["result"][0].get("data", [])
            print(f"Data: {d}")

# Check chart 91
print("\n" + "=" * 70)
print("CHART 91: Jumlah Mahasiswa Aktif per Semester")
print("=" * 70)
r = s.get(f"{BASE}/api/v1/chart/91")
c = r.json()["result"]
print(f"viz_type: {c['viz_type']}")
params = json.loads(c["params"]) if c["params"] else {}
print(f"params: {json.dumps(params, indent=2)}")
qc_str = c.get("query_context")
if qc_str:
    qc = json.loads(qc_str)
    print(f"query: {json.dumps(qc['queries'], indent=2)}")
    r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
    if r2.status_code == 200:
        data = r2.json()
        if "result" in data and data["result"]:
            d = data["result"][0].get("data", [])
            print(f"Data: {d}")

# Check dataset 5 schema
print("\n" + "=" * 70)
print("DATASET 5 SCHEMA")
print("=" * 70)
r = s.get(f"{BASE}/api/v1/dataset/5")
ds = r.json()["result"]
for col in ds.get("columns", []):
    print(f"  {col['column_name']}: {col.get('type', '?')}")
