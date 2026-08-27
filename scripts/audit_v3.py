"""
Full audit of all charts - current state, params, and data
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

chart_ids = [66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,91,100]

for cid in sorted(chart_ids):
    r = s.get(f"{BASE}/api/v1/chart/{cid}")
    c = r.json()["result"]
    name = c["slice_name"]
    viz = c["viz_type"]
    ds_id = c["datasource_id"]
    params = json.loads(c["params"]) if c["params"] else {}
    qc_str = c.get("query_context")
    
    status = "NO_QC"
    rows = 0
    if qc_str:
        qc = json.loads(qc_str)
        r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
        if r2.status_code == 200:
            data = r2.json()
            if "result" in data and data["result"]:
                rows = data["result"][0].get("rowcount", 0)
                status = "OK"
            else:
                status = "EMPTY"
        else:
            status = f"FAIL:{r2.status_code}"
    
    m = params.get("metric", params.get("metrics", "N/A"))
    if isinstance(m, dict):
        m = m.get("label", str(m)[:40])
    elif isinstance(m, list) and m:
        m = str(m[0])[:40] if not isinstance(m[0], dict) else m[0].get("label", str(m[0])[:40])
    
    print(f"Chart {cid:4d}: {viz:25s} | {status:8s} | {rows:>5}r | ds={ds_id} | {name}")
