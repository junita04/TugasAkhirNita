"""
FULL VALIDATION: Test all 26 charts using their stored query_context
"""
import requests
import json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login",
               json={"username": "admin", "password": "change-me", "provider": "db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r0 = s.get(f"{BASE}/api/v1/security/csrf_token/")
    s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": BASE})
    return s

def main():
    s = api()
    
    print("=" * 90)
    print("FULL VALIDATION: ALL 26 CHARTS")
    print("=" * 90)
    
    ok = 0
    fail = 0
    
    for cid in range(1, 27):
        r = s.get(f"{BASE}/api/v1/chart/{cid}")
        if r.status_code != 200:
            print(f"  Chart {cid:2d}: NOT FOUND (HTTP {r.status_code})")
            fail += 1
            continue
        
        c = r.json()["result"]
        name = c.get("slice_name", "?")
        viz = c.get("viz_type", "?")
        ds_id = c.get("datasource_id")
        ds_type = c.get("datasource_type")
        qc_str = c.get("query_context")
        params_str = c.get("params", "{}")
        
        # Check query_context exists
        if not qc_str:
            print(f"  Chart {cid:2d}: NO QUERY_CONTEXT - {name}")
            fail += 1
            continue
        
        qc = json.loads(qc_str)
        queries = qc.get("queries", [])
        
        if not queries:
            print(f"  Chart {cid:2d}: EMPTY QUERIES - {name}")
            fail += 1
            continue
        
        # Check datasource exists
        ds_check = s.get(f"{BASE}/api/v1/dataset/{ds_id}")
        ds_ok = ds_check.status_code == 200
        
        # Test chart data
        r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
        
        if r2.status_code == 200:
            data = r2.json()
            if "result" in data and data["result"]:
                rc = data["result"][0].get("rowcount", "?")
                print(f"  Chart {cid:2d}: OK ({rc:>5} rows) | ds={ds_id} | {viz:20s} | {name}")
                ok += 1
            else:
                print(f"  Chart {cid:2d}: OK (empty result) | ds={ds_id} | {viz:20s} | {name}")
                ok += 1
        else:
            try:
                err = r2.json().get("message", "")[:80]
            except:
                err = r2.text[:80]
            print(f"  Chart {cid:2d}: FAIL (HTTP {r2.status_code}) | ds={ds_id} | {viz:20s} | {name}: {err}")
            fail += 1
    
    print(f"\n{'='*90}")
    print(f"RESULT: {ok}/{ok+fail} charts render data correctly")
    print(f"{'='*90}")

if __name__ == "__main__":
    main()
