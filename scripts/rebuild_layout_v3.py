"""
Rebuild dashboard layout with 6 professional sections.
All charts properly sized for readability.
"""
import requests
import json

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

charts = {
    66: "Total Mahasiswa", 67: "Mahasiswa Aktif", 68: "Mahasiswa Lulus",
    69: "Tepat Waktu (Aktual)", 70: "Terlambat (Aktual)",
    71: "Jumlah Mahasiswa per Angkatan", 72: "Distribusi Jenis Kelamin",
    73: "Distribusi Status Mahasiswa",
    74: "Rata-rata IPK per Angkatan (Lulus)", 75: "Rata-rata Total SKS per Angkatan (Lulus)",
    76: "Rata-rata Selisih SKS per Angkatan (Lulus)", 77: "Rata-rata Lama Studi per Angkatan (Lulus)",
    78: "Status Kelulusan Aktual (Tepat Waktu vs Terlambat)",
    79: "Status Kelulusan per Angkatan (Stacked)", 80: "Persentase Tepat Waktu per Angkatan",
    81: "Model Accuracy (%)", 82: "Model F1 Score (%)",
    83: "Model Precision (%)", 84: "Model Recall (%)",
    85: "Confusion Matrix", 86: "Classification Report",
    87: "Prediksi ML per Angkatan (Aktif)", 88: "Distribusi Prediksi ML (Mahasiswa Aktif)",
    89: "Rata-rata Selisih SKS per Semester (Aktif)",
    91: "Jumlah Mahasiswa Aktif per Semester",
    100: "Distribusi IPK Mahasiswa Aktif",
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
    """chart_rows: list of lists, each inner list is [chart_id, ...] for one row"""
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
        "meta": {"text": title, "headerFontColor": "#C41E3A", "headerFontSize": 0.6},
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

# ---- SECTION 1: Ringkasan Akademik ----
# 5 KPIs in one row: 5 items at width=2 each = 10, need 12
# Use: 4 items at width=3 = 12, then 1 item alone
# Better: use 3+3+3+3 = 12 for first 4, and put 5th in same row at width=3
# But 5*3=15 > 12. So: row1=4 items (3w each=12), row2=1 item (3w)
add_section(1, "Ringkasan Akademik", [
    [66, 67, 68, 69],  # 4 KPIs at width=3
    [70],               # Terlambat at width=3
])

# ---- SECTION 2: Profil Mahasiswa ----
add_section(2, "Profil Mahasiswa", [
    [71, 72, 73],  # Bar + 2 Pies at width=4
])

# ---- SECTION 3: Profil Akademik ----
add_section(3, "Profil Akademik", [
    [74, 75, 76, 77],  # 4 bars at width=3
    [79, 80],           # Stacked bar + percentage at width=6
])

# ---- SECTION 4: Hasil Evaluasi ML ----
add_section(4, "Hasil Evaluasi Machine Learning", [
    [81, 82, 83, 84],  # 4 KPIs at width=3
    [85, 86],           # Confusion Matrix + Classification Report at width=6
])

# ---- SECTION 5: Hasil Prediksi ----
add_section(5, "Hasil Prediksi Mahasiswa Aktif", [
    [87, 88],      # Bar + Pie at width=6
    [78],           # Status Kelulusan at width=12
])

# ---- SECTION 6: Analisis Mahasiswa Aktif ----
add_section(6, "Analisis Mahasiswa Aktif", [
    [100, 91],     # IPK Histogram + Mahasiswa per Semester at width=6
    [89],           # Selisih SKS per Semester at width=12
])

# Print layout
print("Layout order:")
for i, c in enumerate(position["GRID_ID"]["children"]):
    print(f"  {i}: {c}")

# Update dashboard
r = s.put(f"{BASE}/api/v1/dashboard/3", json={
    "position_json": json.dumps(position),
    "dashboard_title": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa",
})
print(f"\nDashboard updated: {r.status_code}")

# Verify
r2 = s.get(f"{BASE}/api/v1/dashboard/3")
pos = json.loads(r2.json()["result"]["position_json"])
chart_count = 0
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        chart_count += 1
print(f"Charts in layout: {chart_count}")
