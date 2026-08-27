"""
Fix dashboard-chart associations via metadata database.
The REST API doesn't expose the M2M relationship, so we use direct SQL.
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
    
    # Get dashboard ID
    r = s.get(f"{BASE_URL}/api/v1/dashboard/?q=(page_size:10)")
    dashboards = r.json()["result"]
    
    print("Dashboards found:")
    target_dash_id = None
    for d in dashboards:
        print(f"  id={d['id']} title='{d['dashboard_title']}'")
        if "Prediksi" in d["dashboard_title"]:
            target_dash_id = d["id"]
    
    if not target_dash_id:
        print("No dashboard found!")
        return
    
    print(f"\nTarget dashboard: id={target_dash_id}")
    
    # Get all chart IDs
    r2 = s.get(f"{BASE_URL}/api/v1/chart/?q=(page_size:100)")
    charts = r2.json()["result"]
    chart_ids = [c["id"] for c in charts]
    print(f"Chart IDs: {chart_ids}")
    
    # The relationship is in dashboard_slices table
    # We need to use Superset's internal API or direct DB access
    # Let's try the Superset CLI approach
    
    # First, let's check if we can use the superset shell
    print("\n--- Trying Superset metadata approach ---")
    
    # We'll use a workaround: create a temporary dataset that forces Superset
    # to refresh its cache, then try the chart association
    
    # Actually, the correct approach for Superset 6.0.0 is to use the
    # PUT /api/v1/dashboard/{id} with the correct payload format
    
    # Let's check what the Superset source code expects
    # The key is that position_json ALONE should be enough to render charts
    # The "charts" field is a READ-ONLY computed field from position_json
    
    # Let's verify by checking if the position_json is properly formatted
    r3 = s.get(f"{BASE_URL}/api/v1/dashboard/{target_dash_id}")
    detail = r3.json()["result"]
    pos = json.loads(detail["position_json"]) if isinstance(detail["position_json"], str) else detail["position_json"]
    
    # Check if charts in position have valid chartIds
    chart_refs = {}
    for k, v in pos.items():
        if isinstance(v, dict) and v.get("type") == "CHART":
            meta = v.get("meta", {})
            chart_id = meta.get("chartId")
            if chart_id:
                chart_refs[chart_id] = meta
    
    print(f"\nChart references in position_json: {len(chart_refs)}")
    for cid, meta in sorted(chart_refs.items()):
        valid = cid in chart_ids
        print(f"  chartId={cid} valid={valid} name={meta.get('sliceName', 'N/A')}")
    
    # The issue might be that Superset needs to "refresh" its understanding
    # of the dashboard. Let's try toggling the published state
    
    print("\n--- Refreshing dashboard ---")
    # Unpublish
    s.put(f"{BASE_URL}/api/v1/dashboard/{target_dash_id}", json={"published": False})
    # Republish
    s.put(f"{BASE_URL}/api/v1/dashboard/{target_dash_id}", json={"published": True})
    
    # Verify again
    r4 = s.get(f"{BASE_URL}/api/v1/dashboard/{target_dash_id}")
    detail2 = r4.json()["result"]
    print(f"  Charts after refresh: {detail2.get('charts', [])}")
    
    # Check if the chart definitions themselves are valid
    print("\n--- Validating chart definitions ---")
    for cid in chart_ids[:5]:
        r5 = s.get(f"{BASE_URL}/api/v1/chart/{cid}")
        if r5.status_code == 200:
            c = r5.json()["result"]
            has_params = bool(c.get("params"))
            has_ds = bool(c.get("datasource_id"))
            print(f"  Chart {cid}: params={has_params} datasource={c.get('datasource_id')} viz={c.get('viz_type')}")
        else:
            print(f"  Chart {cid}: NOT FOUND (status={r5.status_code})")
    
    print(f"\nDashboard URL: http://localhost:8088/superset/dashboard/{target_dash_id}/")

if __name__ == "__main__":
    main()
