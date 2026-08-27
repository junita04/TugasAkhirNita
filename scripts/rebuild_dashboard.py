"""
REBUILD DASHBOARD: 16 charts, 6 sections, clean storytelling
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

# Only 16 charts
charts = {
    66: "Total Mahasiswa", 67: "Mahasiswa Aktif", 68: "Mahasiswa Lulus",
    69: "Tepat Waktu (Aktual)", 70: "Terlambat (Aktual)",
    71: "Jumlah Mahasiswa per Angkatan", 72: "Distribusi Jenis Kelamin",
    73: "Distribusi Status Mahasiswa",
    74: "Rata-rata IPK per Angkatan (Lulus)",
    79: "Status Kelulusan per Angkatan (Stacked)",
    81: "Model Accuracy (%)", 82: "Model F1 Score (%)",
    83: "Model Precision (%)",
    85: "Confusion Matrix",
    87: "Prediksi ML per Angkatan (Aktif)",
    88: "Distribusi Prediksi ML (Mahasiswa Aktif)",
}

position = {
    "DASHBOARD_VERSION_KEY": "v2",
    "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
    "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
    "HEADER_ID": {
        "type": "HEADER",
        "id": "HEADER_ID",
        "meta": {"text": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa - Institut Teknologi Sumatera"},
    },
}

def add_section(section_idx, title, chart_rows):
    title_row_id = f"ROW-section-{section_idx}"
    position["GRID_ID"]["children"].append(title_row_id)
    position[title_row_id] = {
        "type": "ROW", "id": title_row_id, "children": [],
        "parents": ["ROOT_ID", "GRID_ID"],
        "meta": {"background": "BACKGROUND_TRANSPARENT"},
    }
    title_id = f"HEADER-{section_idx}"
    position[title_row_id]["children"].append(title_id)
    position[title_id] = {
        "type": "HEADER", "id": title_id,
        "meta": {"text": title, "headerFontColor": "#8B1E3F", "headerFontSize": 0.6},
    }

    for row_idx, row_charts in enumerate(chart_rows):
        row_id = f"ROW-{section_idx}-{row_idx}"
        position["GRID_ID"]["children"].append(row_id)
        position[row_id] = {
            "type": "ROW", "id": row_id, "children": [],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        n = len(row_charts)
        width = 12 // n if n > 0 else 12
        for cid in row_charts:
            chart_key = f"CHART-{cid}"
            position[row_id]["children"].append(chart_key)
            position[chart_key] = {
                "type": "CHART", "id": chart_key, "children": [],
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "meta": {"chartId": cid, "width": width, "height": 50, "sliceName": charts.get(cid, f"Chart {cid}")},
            }

# Section 1: Ringkasan Akademik - 5 KPI satu baris
add_section(1, "Ringkasan Akademik", [
    [66, 67, 68, 69, 70],
])

# Section 2: Profil Mahasiswa - 3 chart satu baris
add_section(2, "Profil Mahasiswa", [
    [71, 72, 73],
])

# Section 3: Performa Akademik - 2 chart
add_section(3, "Performa Akademik", [
    [74, 79],
])

# Section 4: Hasil Evaluasi ML - 4 KPI + Confusion Matrix
add_section(4, "Hasil Evaluasi Machine Learning", [
    [81, 82, 83],
    [85],
])

# Section 5: Hasil Prediksi Mahasiswa Aktif
add_section(5, "Hasil Prediksi Mahasiswa Aktif", [
    [87, 88],
])

# Update dashboard
r = s.put(f"{BASE}/api/v1/dashboard/3", json={
    "position_json": json.dumps(position),
    "dashboard_title": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa",
})
print(f"Dashboard updated: {r.status_code}")

# Verify
r2 = s.get(f"{BASE}/api/v1/dashboard/3")
pos = json.loads(r2.json()["result"]["position_json"])
chart_count = sum(1 for v in pos.values() if isinstance(v, dict) and v.get("type") == "CHART")
print(f"Charts in layout: {chart_count}")

# List all charts
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        print(f"  Chart {meta.get('chartId')}: {meta.get('width')}w x {meta.get('height')}h | {meta.get('sliceName')}")
