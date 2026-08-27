"""
Check which charts exist and need restoration
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

# Check charts that were removed from layout but may still exist
check_ids = [75, 76, 77, 78, 80, 81, 82, 83, 84, 86, 89, 91, 100]
for cid in check_ids:
    r = s.get(f"{BASE}/api/v1/chart/{cid}")
    if r.status_code == 200:
        c = r.json()["result"]
        qc_str = c.get("query_context")
        status = "OK" if qc_str else "NO_QC"
        if qc_str:
            qc = json.loads(qc_str)
            r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
            if r2.status_code == 200:
                data = r2.json()
                rc = data["result"][0].get("rowcount", 0) if data.get("result") else 0
                status = f"OK ({rc}r)"
            else:
                status = "FAIL"
        print(f"Chart {cid:4d}: {c['viz_type']:25s} | {status:12s} | {c['slice_name']}")
    else:
        print(f"Chart {cid:4d}: NOT FOUND")
