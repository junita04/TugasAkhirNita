"""
Verify what the Superset frontend actually sees.
Simulate browser behavior: load dashboard -> read position_json -> fetch chart data for each referenced chart.
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
    
    # 1. Load dashboard like browser does
    r = s.get(f"{BASE}/api/v1/dashboard/3")
    dash = r.json()["result"]
    pos = json.loads(dash["position_json"])
    
    # 2. Find all chart references in position_json
    chart_refs = []
    for key, val in pos.items():
        if isinstance(val, dict) and val.get("type") == "CHART":
            meta = val.get("meta", {})
            chart_id = meta.get("chartId")
            if chart_id:
                chart_refs.append(chart_id)
    
    print(f"Dashboard references {len(chart_refs)} charts: {chart_refs}")
    
    # 3. For each referenced chart, fetch its data the way the frontend does
    # The frontend calls GET /api/v1/chart/{id} to get query_context, then POST /api/v1/chart/data
    ok = 0
    fail = 0
    errors = []
    
    for cid in chart_refs:
        # Fetch chart definition
        r1 = s.get(f"{BASE}/api/v1/chart/{cid}")
        if r1.status_code != 200:
            print(f"  Chart {cid}: NOT FOUND via API")
            fail += 1
            errors.append(f"Chart {cid}: NOT FOUND")
            continue
        
        c = r1.json()["result"]
        name = c.get("slice_name", "?")
        qc_str = c.get("query_context")
        
        if not qc_str:
            print(f"  Chart {cid}: NO query_context - {name}")
            fail += 1
            errors.append(f"Chart {cid} ({name}): NO query_context")
            continue
        
        qc = json.loads(qc_str)
        
        # Test chart data
        r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
        if r2.status_code == 200:
            data = r2.json()
            if "result" in data and data["result"]:
                rc = data["result"][0].get("rowcount", "?")
                print(f"  Chart {cid:2d}: OK ({rc:>5} rows) - {name}")
                ok += 1
            else:
                print(f"  Chart {cid:2d}: OK (empty) - {name}")
                ok += 1
        else:
            try:
                err = r2.json().get("message", "")[:80]
            except:
                err = r2.text[:80]
            print(f"  Chart {cid:2d}: FAIL - {name}: {err}")
            fail += 1
            errors.append(f"Chart {cid} ({name}): {err}")
    
    print(f"\n{'='*60}")
    print(f"RESULT: {ok}/{len(chart_refs)} charts render correctly")
    if errors:
        print(f"ERRORS:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("NO ERRORS - Dashboard should render all charts!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
