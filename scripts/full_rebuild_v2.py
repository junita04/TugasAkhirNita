"""
COMPLETE DASHBOARD REBUILD: 20 charts, 5 sections
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

charts = {
    66: "Total Mahasiswa", 67: "Mahasiswa Aktif", 68: "Mahasiswa Lulus",
    69: "Tepat Waktu (Aktual)", 70: "Terlambat (Aktual)",
    71: "Jumlah Mahasiswa per Angkatan", 72: "Distribusi Jenis Kelamin",
    73: "Distribusi Status Mahasiswa",
    74: "Rata-rata IPK per Angkatan (Lulus)",
    75: "Rata-rata Total SKS per Angkatan (Lulus)",
    77: "Rata-rata Lama Studi per Angkatan (Lulus)",
    79: "Status Kelulusan per Angkatan",
    80: "Persentase Tepat Waktu per Angkatan",
    85: "Confusion Matrix",
    86: "Classification Report",
    87: "Prediksi ML per Angkatan (Aktif)",
    88: "Distribusi Prediksi ML (Mahasiswa Aktif)",
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

# Section 1: Ringkasan Akademik - 5 KPI full width
add_section(1, "Ringkasan Akademik", [
    [66, 67, 68, 69, 70],
])

# Section 2: Profil Mahasiswa
add_section(2, "Profil Mahasiswa", [
    [71, 71, 72, 73],  # This won't work - duplicate IDs
])

# Need to redo section 2 manually
# Clear section 2
position["GRID_ID"]["children"] = [c for c in position["GRID_ID"]["children"] if not c.startswith("ROW-section-2") and not c.startswith("ROW-2-") and c != "HEADER-2"]

# Section 2: Row 1 = Bar Angkatan (12w), Row 2 = 2 Donuts (6+6)
title_row_id = "ROW-section-2"
position["GRID_ID"]["children"].append(title_row_id)
position[title_row_id] = {
    "type": "ROW", "id": title_row_id, "children": ["HEADER-2"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"},
}
position["HEADER-2"] = {
    "type": "HEADER", "id": "HEADER-2",
    "meta": {"text": "Profil Mahasiswa", "headerFontColor": "#8B1E3F", "headerFontSize": 0.6},
}

row_id = "ROW-2-0"
position["GRID_ID"]["children"].append(row_id)
position[row_id] = {"type": "ROW", "id": row_id, "children": ["CHART-71"], "parents": ["ROOT_ID", "GRID_ID"], "meta": {"background": "BACKGROUND_TRANSPARENT"}}
position["CHART-71"] = {"type": "CHART", "id": "CHART-71", "children": [], "parents": ["ROOT_ID", "GRID_ID", row_id], "meta": {"chartId": 71, "width": 12, "height": 50, "sliceName": charts[71]}}

row_id = "ROW-2-1"
position["GRID_ID"]["children"].append(row_id)
position[row_id] = {"type": "ROW", "id": row_id, "children": ["CHART-72", "CHART-73"], "parents": ["ROOT_ID", "GRID_ID"], "meta": {"background": "BACKGROUND_TRANSPARENT"}}
position["CHART-72"] = {"type": "CHART", "id": "CHART-72", "children": [], "parents": ["ROOT_ID", "GRID_ID", row_id], "meta": {"chartId": 72, "width": 6, "height": 50, "sliceName": charts[72]}}
position["CHART-73"] = {"type": "CHART", "id": "CHART-73", "children": [], "parents": ["ROOT_ID", "GRID_ID", row_id], "meta": {"chartId": 73, "width": 6, "height": 50, "sliceName": charts[73]}}

# Section 3: Performa Akademik
# Row 1: Status Kelulusan (6w) + Persentase TW (6w)
# Row 2: IPK (4w) + SKS (4w) + Lama Studi (4w)
add_section(3, "Performa Akademik", [
    [79, 80],
    [74, 75, 77],
])

# Section 4: Hasil Evaluasi Model
# Row 1: CM (6w) + CR (6w)
add_section(4, "Hasil Evaluasi Model", [
    [85, 86],
])

# Section 5: Hasil Prediksi Mahasiswa Aktif
# Row 1: Prediksi per Angkatan (6w) + Distribusi (6w)
# Row 2: Aktif per Semester (4w) + IPK Aktif (4w) + Selisih SKS (4w)
add_section(5, "Hasil Prediksi Mahasiswa Aktif", [
    [87, 88],
    [91, 100, 89],
])

# Fix KPI widths
for key, val in position.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        cid = meta.get("chartId")
        if cid == 66: meta["width"] = 3
        elif cid == 67: meta["width"] = 3
        elif cid in [68, 69, 70]: meta["width"] = 2

# Update dashboard
r = s.put(f"{BASE}/api/v1/dashboard/3", json={
    "position_json": json.dumps(position),
    "dashboard_title": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa",
})
print(f"Dashboard updated: {r.status_code}")

# Verify
r2 = s.get(f"{BASE}/api/v1/dashboard/3")
pos = json.loads(r2.json()["result"]["position_json"])
chart_count = 0
total_w = 0
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        chart_count += 1
        w = meta.get("width", 0)
        total_w += w
        print(f"  Chart {meta.get('chartId')}: {w}w | {meta.get('sliceName')}")
print(f"\nTotal charts: {chart_count}")
print(f"Total width: {total_w}")
