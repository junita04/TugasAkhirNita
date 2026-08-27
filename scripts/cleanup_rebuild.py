"""
CLEANUP + REBUILD: Delete invalid datasets, delete old dashboard,
rebuild dashboard with all 26 charts and proper position_json.
"""

import requests
import json
import time

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
    print("CLEANUP + REBUILD")
    print("=" * 70)
    
    # 1. Delete invalid datasets
    print("\n--- Deleting invalid datasets ---")
    r = s.get(f"{BASE_URL}/api/v1/dataset/?q=(page_size:100)")
    datasets = r.json()["result"]
    
    invalid_names = {"gold_program_studi", "prediction_result", "gold_mahasiswa", "gold_kurikulum"}
    for ds in datasets:
        if ds["table_name"] in invalid_names:
            r2 = s.delete(f"{BASE_URL}/api/v1/dataset/{ds['id']}")
            print(f"  Deleted {ds['table_name']} (id={ds['id']}): status={r2.status_code}")
    
    time.sleep(1)
    
    # 2. Delete old dashboards
    print("\n--- Deleting old dashboards ---")
    r3 = s.get(f"{BASE_URL}/api/v1/dashboard/?q=(page_size:50)")
    for d in r3.json()["result"]:
        r4 = s.delete(f"{BASE_URL}/api/v1/dashboard/{d['id']}")
        print(f"  Deleted dashboard {d['id']}: status={r4.status_code}")
    
    time.sleep(1)
    
    # 3. Get valid datasets
    print("\n--- Valid datasets ---")
    r5 = s.get(f"{BASE_URL}/api/v1/dataset/?q=(page_size:100)")
    valid_ds = {}
    for ds in r5.json()["result"]:
        if ds["table_name"] not in invalid_names:
            valid_ds[ds["table_name"]] = ds["id"]
            print(f"  {ds['table_name']}: id={ds['id']}")
    
    # 4. Get all charts
    print("\n--- Charts ---")
    r6 = s.get(f"{BASE_URL}/api/v1/chart/?q=(page_size:100)")
    charts = r6.json()["result"]
    chart_ids = [c["id"] for c in charts]
    print(f"  Total charts: {len(chart_ids)}")
    print(f"  Chart IDs: {sorted(chart_ids)}")
    
    # 5. Build position_json with ALL 26 charts
    print("\n--- Building position_json ---")
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
        "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID", "meta": {"text": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa"}},
    }
    
    row_n = [0]
    chart_n = [0]
    
    def header(text):
        row_n[0] += 1
        k = f"ROW-h{row_n[0]}"
        position[k] = {"type": "ROW", "id": k, "children": [], "parents": ["ROOT_ID", "GRID_ID"], "meta": {"text": text, "background": "BACKGROUND_TRANSPARENT"}}
        position["GRID_ID"]["children"].append(k)
        return k
    
    def row():
        row_n[0] += 1
        k = f"ROW-{row_n[0]}"
        position[k] = {"type": "ROW", "id": k, "children": [], "parents": ["ROOT_ID", "GRID_ID"], "meta": {"background": "BACKGROUND_TRANSPARENT"}}
        position["GRID_ID"]["children"].append(k)
        return k
    
    def chart(cid, parent, w=6, h=50):
        chart_n[0] += 1
        k = f"CHART-{chart_n[0]}"
        position[k] = {"type": "CHART", "id": k, "children": [], "parents": ["ROOT_ID", "GRID_ID", parent], "meta": {"width": w, "height": h, "chartId": cid, "sliceName": f"Chart {cid}"}}
        position[parent]["children"].append(k)
    
    # Layout
    header("Dashboard Prediksi Tingkat Kelulusan Mahasiswa")
    
    # Section 1: KPI (charts 1-5)
    header("1. Ringkasan Akademik")
    r1 = row()
    chart(1, r1, 2, 20)
    chart(2, r1, 2, 20)
    chart(3, r1, 2, 20)
    chart(4, r1, 3, 20)
    chart(5, r1, 3, 20)
    
    # Section 2: Profil (charts 6-8)
    header("2. Profil Mahasiswa")
    r2 = row()
    chart(6, r2, 8, 50)
    chart(7, r2, 4, 50)
    r3 = row()
    chart(8, r3, 12, 50)
    
    # Section 3: Akademik (charts 9-12)
    header("3. Perkembangan Akademik")
    r4 = row()
    chart(9, r4, 6, 50)
    chart(10, r4, 6, 50)
    r5 = row()
    chart(11, r5, 6, 50)
    chart(12, r5, 6, 50)
    
    # Section 4: Kelulusan (charts 13-15)
    header("4. Status Kelulusan")
    r6 = row()
    chart(13, r6, 4, 50)
    chart(14, r6, 8, 50)
    r7 = row()
    chart(15, r7, 12, 50)
    
    # Section 5: ML (charts 16-23)
    header("5. Hasil Machine Learning")
    r8 = row()
    chart(16, r8, 3, 20)
    chart(17, r8, 3, 20)
    chart(18, r8, 3, 20)
    chart(19, r8, 3, 20)
    r9 = row()
    chart(20, r9, 6, 50)
    chart(21, r9, 6, 50)
    r10 = row()
    chart(22, r10, 6, 50)
    chart(23, r10, 6, 50)
    
    # Section 6: Aktif (charts 24-26)
    header("6. Analisis Mahasiswa Aktif")
    r11 = row()
    chart(24, r11, 4, 50)
    chart(25, r11, 4, 50)
    chart(26, r11, 4, 50)
    
    # Verify all charts are in position
    pos_charts = set()
    for k, v in position.items():
        if isinstance(v, dict) and v.get("type") == "CHART":
            meta = v.get("meta", {})
            cid = meta.get("chartId")
            if cid:
                pos_charts.add(cid)
    
    missing = set(chart_ids) - pos_charts
    print(f"  Charts in position: {len(pos_charts)}")
    print(f"  Missing: {sorted(missing) if missing else 'none'}")
    
    # 6. Create dashboard
    print("\n--- Creating dashboard ---")
    r7 = s.post(f"{BASE_URL}/api/v1/dashboard/", json={
        "dashboard_title": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa",
        "slug": "dashboard-prediksi-kelulusan",
        "published": True,
        "position_json": json.dumps(position),
    })
    
    if r7.status_code not in (200, 201):
        print(f"  Error: {r7.status_code} {r7.text[:300]}")
        return
    
    dash_id = r7.json()["id"]
    print(f"  Dashboard ID: {dash_id}")
    
    # 7. Verify
    time.sleep(1)
    r8 = s.get(f"{BASE_URL}/api/v1/dashboard/{dash_id}")
    detail = r8.json()["result"]
    print(f"  Title: {detail['dashboard_title']}")
    print(f"  Charts field: {detail.get('charts', [])}")
    print(f"  Published: {detail.get('published', False)}")
    
    # 8. Test chart rendering
    print("\n--- Testing chart rendering ---")
    for cid in sorted(chart_ids)[:5]:
        r9 = s.get(f"{BASE_URL}/api/v1/chart/{cid}")
        c = r9.json()["result"]
        ds_id = c.get("datasource_id")
        has_params = bool(c.get("params"))
        print(f"  Chart {cid}: datasource={ds_id} params={has_params} viz={c.get('viz_type')}")
    
    # 9. Test a query
    print("\n--- Testing queries ---")
    test_sql = "SELECT COUNT(*) as cnt FROM iceberg.gold.data_referensi_mahasiswa"
    r10 = s.post(f"{BASE_URL}/api/v1/sqllab/execute/", json={"database_id": 1, "sql": test_sql, "runAsync": False})
    if r10.status_code == 200:
        data = r10.json()
        if "result" in data:
            cnt = data["result"]["data"][0]["cnt"]
            print(f"  Query test: {cnt} rows - OK")
    
    print(f"\n{'='*70}")
    print(f"DASHBOARD URL: http://localhost:8088/superset/dashboard/{dash_id}/")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
