"""
RECREATE DASHBOARD with correct API usage
==========================================
Find the right way to associate charts with dashboards in Superset 6.0.0.
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
    print("RECREATING DASHBOARD")
    print("=" * 70)
    
    # Get all chart IDs
    r = s.get(f"{BASE_URL}/api/v1/chart/?q=(page_size:100)")
    charts = r.json()["result"]
    all_chart_ids = [c["id"] for c in charts]
    print(f"Charts available: {all_chart_ids}")
    
    # Build position_json
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
        "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID", "meta": {"text": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa"}},
    }
    
    row_counter = [0]
    chart_counter = [0]
    
    def add_header(text):
        row_counter[0] += 1
        key = f"ROW-h{row_counter[0]}"
        position[key] = {
            "type": "ROW", "id": key,
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"text": text, "background": "BACKGROUND_TRANSPARENT"},
        }
        position["GRID_ID"]["children"].append(key)
        return key
    
    def add_row():
        row_counter[0] += 1
        key = f"ROW-{row_counter[0]}"
        position[key] = {
            "type": "ROW", "id": key,
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        position["GRID_ID"]["children"].append(key)
        return key
    
    def add_chart(chart_id, parent_row, width=6, height=50):
        chart_counter[0] += 1
        key = f"CHART-{chart_counter[0]}"
        position[key] = {
            "type": "CHART", "id": key,
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID", parent_row],
            "meta": {"width": width, "height": height, "chartId": chart_id, "sliceName": f"Chart {chart_id}"},
        }
        position[parent_row]["children"].append(key)
    
    # Build layout
    add_header("Dashboard Prediksi Tingkat Kelulusan Mahasiswa")
    
    # Section 1: KPI
    add_header("1. Ringkasan Akademik")
    r1 = add_row()
    for cid in all_chart_ids[:5]:
        add_chart(cid, r1, width=2, height=20)
    
    # Section 2: Profil
    add_header("2. Profil Mahasiswa")
    r2 = add_row()
    add_chart(6, r2, width=8, height=50)
    add_chart(7, r2, width=4, height=50)
    r3 = add_row()
    add_chart(8, r3, width=6, height=50)
    
    # Section 3: Akademik
    add_header("3. Perkembangan Akademik")
    r4 = add_row()
    add_chart(9, r4, width=6, height=50)
    add_chart(10, r4, width=6, height=50)
    r5 = add_row()
    add_chart(11, r5, width=6, height=50)
    add_chart(12, r5, width=6, height=50)
    
    # Section 4: Kelulusan
    add_header("4. Status Kelulusan")
    r6 = add_row()
    add_chart(13, r6, width=4, height=50)
    add_chart(14, r6, width=8, height=50)
    r7 = add_row()
    add_chart(15, r7, width=12, height=50)
    
    # Section 5: ML
    add_header("5. Hasil Machine Learning")
    r8 = add_row()
    for cid in all_chart_ids[15:19]:
        add_chart(cid, r8, width=3, height=20)
    r9 = add_row()
    add_chart(20, r9, width=6, height=50)
    add_chart(21, r9, width=6, height=50)
    r10 = add_row()
    add_chart(22, r10, width=6, height=50)
    add_chart(23, r10, width=6, height=50)
    
    # Section 6: Aktif
    add_header("6. Analisis Mahasiswa Aktif")
    r11 = add_row()
    add_chart(24, r11, width=4, height=50)
    add_chart(25, r11, width=4, height=50)
    add_chart(26, r11, width=4, height=50)
    
    # Try creating dashboard WITHOUT chart_ids first, then update
    print("\n--- Creating dashboard (no chart_ids) ---")
    create_payload = {
        "dashboard_title": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa",
        "slug": "dashboard-prediksi-kelulusan",
        "published": True,
        "position_json": json.dumps(position),
    }
    r1 = s.post(f"{BASE_URL}/api/v1/dashboard/", json=create_payload)
    print(f"  Status: {r1.status_code}")
    if r1.status_code not in (200, 201):
        print(f"  Error: {r1.text[:300]}")
        return
    
    dash_id = r1.json()["id"]
    print(f"  Dashboard ID: {dash_id}")
    
    # Now try to associate charts via different methods
    print(f"\n--- Associating charts to dashboard {dash_id} ---")
    
    # Method: PUT with the correct field name
    # In Superset 6.0.0, the field might be 'owners' or we need to use the 
    # dashboard_slices table directly
    
    # Let's check what fields are allowed on PUT
    r_test = s.put(f"{BASE_URL}/api/v1/dashboard/{dash_id}", json={
        "dashboard_title": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa",
    })
    print(f"  PUT test: {r_test.status_code}")
    
    # Try the query endpoint to check chart associations
    r_charts = s.get(f"{BASE_URL}/api/v1/dashboard/{dash_id}/charts/")
    print(f"  GET charts: {r_charts.status_code}")
    if r_charts.status_code == 200:
        print(f"  Charts: {r_charts.json()}")
    
    # Check if there's a M2M endpoint
    r_m2m = s.get(f"{BASE_URL}/api/v1/dashboard/{dash_id}/slices/")
    print(f"  GET slices: {r_m2m.status_code}")
    
    # Verify the dashboard
    r_verify = s.get(f"{BASE_URL}/api/v1/dashboard/{dash_id}")
    detail = r_verify.json()["result"]
    print(f"\n--- Dashboard Verification ---")
    print(f"  Title: {detail['dashboard_title']}")
    print(f"  Charts: {detail.get('charts', [])}")
    print(f"  URL: http://localhost:8088{detail.get('url', '')}")
    
    return dash_id

if __name__ == "__main__":
    main()
