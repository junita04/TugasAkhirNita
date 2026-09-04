"""
Test chart data query via Superset API.
"""
import requests
import json

SUPERSET = "http://localhost:8088"

# Login
r = requests.post(f"{SUPERSET}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
token = r.json().get("access_token")
print(f"Login: OK")

# Test each chart
chart_ids = [127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144]

for cid in chart_ids:
    # Get chart info
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{SUPERSET}/api/v1/chart/{cid}", headers=headers)
    if r.status_code != 200:
        print(f"Chart {cid}: FAILED to get info ({r.status_code})")
        continue
    
    chart_data = r.json().get("result", {})
    name = chart_data.get("slice_name", "?")
    viz_type = chart_data.get("viz_type", "?")
    
    # Try to get chart data
    r2 = requests.get(f"{SUPERSET}/api/v1/chart/{cid}/data/", headers=headers, params={"force": "true"})
    status = "OK" if r2.status_code == 200 else f"FAIL({r2.status_code})"
    
    if r2.status_code == 200:
        data = r2.json()
        if "result" in data:
            result = data["result"]
            if isinstance(result, list) and len(result) > 0:
                row_count = len(result[0].get("data", []))
                print(f"  Chart {cid:3d} ({name[:30]:30s}) {viz_type:25s} {status} rows={row_count}")
            else:
                print(f"  Chart {cid:3d} ({name[:30]:30s}) {viz_type:25s} {status} (empty result)")
        else:
            print(f"  Chart {cid:3d} ({name[:30]:30s}) {viz_type:25s} {status} (no result key)")
    else:
        error_msg = r2.text[:100] if r2.text else "no error msg"
        print(f"  Chart {cid:3d} ({name[:30]:30s}) {viz_type:25s} {status} {error_msg}")
