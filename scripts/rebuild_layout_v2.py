"""
Rebuild dashboard with professional layout, color-coded sections, and proper styling.
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

# Chart ID -> name mapping
charts = {
    66: "Total Mahasiswa",
    67: "Mahasiswa Aktif",
    68: "Mahasiswa Lulus",
    69: "Tepat Waktu (Aktual)",
    70: "Terlambat (Aktual)",
    71: "Jumlah Mahasiswa per Angkatan",
    72: "Distribusi Jenis Kelamin",
    73: "Distribusi Status Mahasiswa",
    74: "Rata-rata IPK per Angkatan (Lulus)",
    75: "Rata-rata Total SKS per Angkatan (Lulus)",
    76: "Rata-rata Selisih SKS per Angkatan (Lulus)",
    77: "Rata-rata Lama Studi per Angkatan (Lulus)",
    78: "Status Kelulusan Aktual (Tepat Waktu vs Terlambat)",
    79: "Status Kelulusan per Angkatan (Stacked)",
    80: "Persentase Tepat Waktu per Angkatan",
    81: "Model Accuracy (%)",
    82: "Model F1 Score (%)",
    83: "Model Precision (%)",
    84: "Model Recall (%)",
    85: "Confusion Matrix",
    86: "Classification Report",
    87: "Prediksi ML per Angkatan (Aktif)",
    88: "Distribusi Prediksi ML (Mahasiswa Aktif)",
    89: "Rata-rata Selisih SKS per Semester (Aktif)",
    91: "Jumlah Mahasiswa Aktif per Semester",
    100: "Distribusi IPK Mahasiswa Aktif",
}

# Build position_json
position = {
    "DASHBOARD_VERSION_KEY": "v2",
    "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
    "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
    "HEADER_ID": {
        "type": "HEADER",
        "id": "HEADER_ID",
        "meta": {"text": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa"},
    },
}

def add_section(section_idx, title, chart_ids, row_height=50):
    """Add a section with title row and chart rows."""
    # Section title row
    title_row_id = f"ROW-title-{section_idx}"
    position["GRID_ID"]["children"].append(title_row_id)
    position[title_row_id] = {
        "type": "ROW",
        "id": title_row_id,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID"],
        "meta": {"background": "BACKGROUND_TRANSPARENT"},
    }
    title_id = f"HEADER-section-{section_idx}"
    position[title_row_id]["children"].append(title_id)
    position[title_id] = {
        "type": "HEADER",
        "id": title_id,
        "meta": {"text": title, "headerFontColor": "#1FA8C9", "headerFontSize": 0.6},
    }

    # Chart rows (max 4 charts per row for KPIs, 3 for others)
    charts_per_row = 4
    for i in range(0, len(chart_ids), charts_per_row):
        row_charts = chart_ids[i:i+charts_per_row]
        row_id = f"ROW-{section_idx}-{i//charts_per_row}"
        position["GRID_ID"]["children"].append(row_id)
        position[row_id] = {
            "type": "ROW",
            "id": row_id,
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }

        n = len(row_charts)
        width = 12 // n if n > 0 else 12

        for cid in row_charts:
            chart_key = f"CHART-{cid}"
            position[row_id]["children"].append(chart_key)
            position[chart_key] = {
                "type": "CHART",
                "id": chart_key,
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "meta": {
                    "chartId": cid,
                    "width": width,
                    "height": row_height,
                    "sliceName": charts.get(cid, f"Chart {cid}"),
                },
            }

# Section 1: Ringkasan Akademik - 5 KPI cards
add_section(1, "Ringkasan Akademik", [66, 67, 68, 69, 70], row_height=40)

# Section 2: Profil Akademik - 3 charts
add_section(2, "Profil Akademik", [71, 72, 73], row_height=50)

# Section 3: Analisis Kelulusan - 6 charts
add_section(3, "Analisis Kelulusan", [74, 75, 76, 77, 79, 80], row_height=50)

# Section 4: Hasil Evaluasi ML - 6 charts
add_section(4, "Hasil Evaluasi Machine Learning", [81, 82, 83, 84, 85, 86], row_height=50)

# Section 5: Hasil Prediksi - 3 charts
add_section(5, "Hasil Prediksi Mahasiswa Aktif", [87, 88, 78], row_height=50)

# Section 6: Analisis Mahasiswa Aktif - 3 charts
add_section(6, "Analisis Mahasiswa Aktif", [100, 91, 89], row_height=50)

# Update dashboard
r = s.put(f"{BASE}/api/v1/dashboard/3", json={
    "position_json": json.dumps(position),
    "dashboard_title": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa",
})
print(f"Dashboard updated: {r.status_code}")

# Verify
r2 = s.get(f"{BASE}/api/v1/dashboard/3")
dash = r2.json()["result"]
pos = json.loads(dash.get("position_json", "{}"))
chart_refs = set()
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        chart_id = meta.get("chartId")
        if chart_id:
            chart_refs.add(chart_id)
print(f"Charts in layout: {len(chart_refs)}")
print(f"Chart IDs: {sorted(chart_refs)}")
