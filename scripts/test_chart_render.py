"""
Test if charts can render data after column refresh.
"""

import requests
import json

BASE_URL = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/v1/security/login",
               json={"username": "admin", "password": "change-me", "provider": "db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r0 = s.get(f"{BASE_URL}/api/v1/security/csrf_token/")
    s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": BASE_URL})
    return s

def main():
    s = api()
    
    print("=" * 70)
    print("CHART RENDER TEST")
    print("=" * 70)
    
    # Get all charts
    r = s.get(f"{BASE_URL}/api/v1/chart/?q=(page_size:100)")
    charts = r.json()["result"]
    
    success = 0
    failed = 0
    
    for c in charts:
        cid = c["id"]
        name = c["slice_name"]
        viz = c["viz_type"]
        ds_id = c.get("datasource_id")
        
        # Test chart data endpoint
        r2 = s.get(f"{BASE_URL}/api/v1/chart/{cid}/data/")
        status = r2.status_code
        
        if status == 200:
            try:
                data = r2.json()
                if "result" in data:
                    result = data["result"]
                    if isinstance(result, dict):
                        rowcount = result.get("rowcount", 0)
                        print(f"  Chart {cid:2d} [{viz:20s}] {name:45s} -> OK (rows={rowcount})")
                        success += 1
                    else:
                        print(f"  Chart {cid:2d} [{viz:20s}] {name:45s} -> OK (result type={type(result).__name__})")
                        success += 1
                else:
                    print(f"  Chart {cid:2d} [{viz:20s}] {name:45s} -> NO RESULT KEY")
                    failed += 1
            except Exception as e:
                print(f"  Chart {cid:2d} [{viz:20s}] {name:45s} -> PARSE ERROR: {e}")
                failed += 1
        else:
            try:
                err = r2.json()
                msg = err.get("message", str(err)[:100])
            except:
                msg = r2.text[:100]
            print(f"  Chart {cid:2d} [{viz:20s}] {name:45s} -> FAILED (status={status}): {msg}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"RESULTS: {success} OK, {failed} FAILED out of {len(charts)} total")
    print(f"{'='*70}")
    
    # Also test dashboard
    print("\n--- Dashboard test ---")
    r3 = s.get(f"{BASE_URL}/api/v1/dashboard/3")
    if r3.status_code == 200:
        d = r3.json()["result"]
        print(f"  Dashboard: {d['dashboard_title']}")
        print(f"  URL: http://localhost:8088{d.get('url', '')}")
        print(f"  Charts field: {d.get('charts', [])}")

if __name__ == "__main__":
    main()
