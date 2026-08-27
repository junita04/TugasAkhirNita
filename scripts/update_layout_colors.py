"""
Update layout for Analisis Mahasiswa Aktif section + apply maroon colors
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

# Update chart 89 params (Selisih SKS)
print("Updating chart 89...")
r = s.get(f"{BASE}/api/v1/chart/89")
c = r.json()["result"]
params = json.loads(c["params"])
params["show_bar_value"] = True
params["rich_tooltip"] = True
params["color_scheme"] = "supersetCategory10"
s.put(f"{BASE}/api/v1/chart/89", json={"params": json.dumps(params)})
print(f"  Chart 89 updated")

# Update chart 91 params (Mahasiswa per Semester)
print("Updating chart 91...")
r = s.get(f"{BASE}/api/v1/chart/91")
c = r.json()["result"]
params = json.loads(c["params"])
params["show_bar_value"] = True
params["rich_tooltip"] = True
params["color_scheme"] = "supersetCategory10"
s.put(f"{BASE}/api/v1/chart/91", json={"params": json.dumps(params)})
print(f"  Chart 91 updated")

# Update all bar charts with maroon color hints
bar_charts = [71, 74, 75, 76, 77, 79, 80, 87]
for cid in bar_charts:
    r = s.get(f"{BASE}/api/v1/chart/{cid}")
    c = r.json()["result"]
    params = json.loads(c["params"])
    params["color_scheme"] = "supersetCategory10"
    params["show_bar_value"] = True
    params["rich_tooltip"] = True
    s.put(f"{BASE}/api/v1/chart/{cid}", json={"params": json.dumps(params)})
    print(f"  Chart {cid} updated")

# Update pie charts
pie_charts = [72, 73, 78, 88]
for cid in pie_charts:
    r = s.get(f"{BASE}/api/v1/chart/{cid}")
    c = r.json()["result"]
    params = json.loads(c["params"])
    params["color_scheme"] = "supersetCategory10"
    params["show_legend"] = True
    params["show_labels"] = True
    params["label_type"] = "key_value_percent"
    params["donut"] = True
    params["innerRadius"] = 40
    params["outerRadius"] = 80
    s.put(f"{BASE}/api/v1/chart/{cid}", json={"params": json.dumps(params)})
    print(f"  Chart {cid} updated")

# Update dashboard layout
print("\nUpdating dashboard layout...")
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

# Section 1: Ringkasan Akademik
add_section(1, "Ringkasan Akademik", [
    [66, 67, 68, 69],
    [70],
])

# Section 2: Profil Mahasiswa
add_section(2, "Profil Mahasiswa", [
    [71, 72, 73],
])

# Section 3: Profil Akademik
add_section(3, "Profil Akademik", [
    [74, 75, 76],
    [77, 79, 80],
])

# Section 4: Hasil Evaluasi ML
add_section(4, "Hasil Evaluasi Machine Learning", [
    [81, 82, 83, 84],
    [85, 86],
])

# Section 5: Hasil Prediksi
add_section(5, "Hasil Prediksi Mahasiswa Aktif", [
    [87, 88],
    [78],
])

# Section 6: Analisis Mahasiswa Aktif
add_section(6, "Analisis Mahasiswa Aktif", [
    [100, 91],
    [89],
])

# Update dashboard
r = s.put(f"{BASE}/api/v1/dashboard/3", json={
    "position_json": json.dumps(position),
    "dashboard_title": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa",
})
print(f"Dashboard updated: {r.status_code}")
