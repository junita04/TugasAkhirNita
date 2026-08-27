"""
FIX DASHBOARD: Associate charts to dashboard
=============================================
The root cause is that charts are not linked to the dashboard's
'slices' relationship. position_json alone is not enough.
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
    print("FIXING DASHBOARD CHART ASSOCIATIONS")
    print("=" * 70)
    
    # Step 1: Get all chart IDs
    r = s.get(f"{BASE_URL}/api/v1/chart/?q=(page_size:100)")
    charts = r.json()["result"]
    all_chart_ids = [c["id"] for c in charts]
    print(f"\nAll chart IDs: {all_chart_ids}")
    print(f"Total charts: {len(all_chart_ids)}")
    
    # Step 2: Get current dashboard
    r = s.get(f"{BASE_URL}/api/v1/dashboard/1")
    dash = r.json()["result"]
    print(f"\nCurrent dashboard: '{dash['dashboard_title']}'")
    print(f"Current charts field: {dash.get('charts', [])}")
    
    # Step 3: Update dashboard to include chart associations
    # The key insight: Superset API uses 'slices' or 'chart_ids' to link charts
    # We need to find the right field name
    
    # Try different approaches
    print("\n--- Attempt 1: Update with chart_ids ---")
    r1 = s.put(f"{BASE_URL}/api/v1/dashboard/1", json={"chart_ids": all_chart_ids})
    print(f"  Status: {r1.status_code}")
    if r1.status_code != 200:
        print(f"  Response: {r1.text[:300]}")
    
    # Check if it worked
    r_check = s.get(f"{BASE_URL}/api/v1/dashboard/1")
    charts_after = r_check.json()["result"].get("charts", [])
    print(f"  Charts after: {charts_after}")
    
    if not charts_after:
        print("\n--- Attempt 2: Update with slices ---")
        r2 = s.put(f"{BASE_URL}/api/v1/dashboard/1", json={"slices": all_chart_ids})
        print(f"  Status: {r2.status_code}")
        if r2.status_code != 200:
            print(f"  Response: {r2.text[:300]}")
        
        r_check2 = s.get(f"{BASE_URL}/api/v1/dashboard/1")
        charts_after2 = r_check2.json()["result"].get("charts", [])
        print(f"  Charts after: {charts_after2}")
    
    if not charts_after and not charts_after2:
        print("\n--- Attempt 3: Delete and recreate with proper associations ---")
        
        # Get current position_json
        r_pos = s.get(f"{BASE_URL}/api/v1/dashboard/1")
        position = r_pos.json()["result"].get("position_json", "{}")
        
        # Delete old dashboard
        r_del = s.delete(f"{BASE_URL}/api/v1/dashboard/1")
        print(f"  Delete old dashboard: {r_del.status_code}")
        
        # Create new dashboard with chart_ids
        new_dash = {
            "dashboard_title": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa",
            "slug": "dashboard-prediksi-kelulusan",
            "published": True,
            "position_json": position,
            "chart_ids": all_chart_ids,
        }
        r_new = s.post(f"{BASE_URL}/api/v1/dashboard/", json=new_dash)
        print(f"  Create new dashboard: {r_new.status_code}")
        if r_new.status_code in (200, 201):
            new_id = r_new.json()["id"]
            print(f"  New dashboard ID: {new_id}")
            
            # Verify
            r_verify = s.get(f"{BASE_URL}/api/v1/dashboard/{new_id}")
            verify = r_verify.json()["result"]
            print(f"  Charts field: {verify.get('charts', [])}")
            print(f"  URL: {verify.get('url', 'N/A')}")
        else:
            print(f"  Response: {r_new.text[:300]}")
    
    # Step 4: Final verification
    print("\n--- FINAL VERIFICATION ---")
    r_all = s.get(f"{BASE_URL}/api/v1/dashboard/?q=(page_size:50)")
    for d in r_all.json()["result"]:
        did = d["id"]
        r_d = s.get(f"{BASE_URL}/api/v1/dashboard/{did}")
        detail = r_d.json()["result"]
        charts_list = detail.get("charts", [])
        pos = json.loads(detail.get("position_json", "{}")) if isinstance(detail.get("position_json"), str) else detail.get("position_json", {})
        pos_charts = [v["meta"]["chartId"] for v in pos.values() if isinstance(v, dict) and v.get("type") == "CHART" and "meta" in v and "chartId" in v.get("meta", {})]
        print(f"  Dashboard {did}: '{detail['dashboard_title']}'")
        print(f"    charts field: {charts_list}")
        print(f"    position charts: {pos_charts}")
        print(f"    Match: {set(charts_list) == set(pos_charts) if charts_list else 'NO CHARTS'}")

if __name__ == "__main__":
    main()
