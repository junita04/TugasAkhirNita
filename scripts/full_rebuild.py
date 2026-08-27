"""
COMPLETE DASHBOARD REBUILD: 16 charts, 5 sections
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
    77: "Rata-rata Lama Studi per Angkatan (Lulus)",
    79: "Status Kelulusan per Angkatan",
    80: "Persentase Tepat Waktu per Angkatan",
    85: "Confusion Matrix",
    86: "Classification Report",
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

# Section 1: Ringkasan Akademik - 5 KPI full width
add_section(1, "Ringkasan Akademik", [
    [66, 67, 68, 69, 70],
])

# Section 2: Profil Mahasiswa
# Row 1: Bar Angkatan (dominant)
# Row 2: 2 donut charts
add_section(2, "Profil Mahasiswa", [
    [71, 71, 72, 73],  # Bar=8w, JK=2w, Status=2w — wait, can't duplicate
])

# Actually: Bar takes 8w, donuts take 2w each
# But 8+2+2=12, and we can't have duplicate chart IDs in same row
# Solution: Bar alone in row 1, donuts in row 2
# Or: Bar=6w, JK=3w, Status=3w

# Let me redo section 2
# Remove the bad section
position["GRID_ID"]["children"] = [c for c in position["GRID_ID"]["children"] if not c.startswith("ROW-section-2") and not c.startswith("ROW-2-")]

# Section 2: Profil Mahasiswa
# Row 1: Bar Angkatan (8w) + Jenis Kelamin (4w) — 12 total
# Actually user wants bar dominant. Let me use: Bar=8w, then 2 donuts in next row

title_row_id = "ROW-section-2"
position["GRID_ID"]["children"].append(title_row_id)
position[title_row_id] = {
    "type": "ROW", "id": title_row_id, "children": [],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"},
}
position[title_row_id]["children"].append("HEADER-2")
position["HEADER-2"] = {
    "type": "HEADER", "id": "HEADER-2",
    "meta": {"text": "Profil Mahasiswa", "headerFontColor": "#8B1E3F", "headerFontSize": 0.6},
}

# Row 2a: Bar Angkatan full width
row_id = "ROW-2-0"
position["GRID_ID"]["children"].append(row_id)
position[row_id] = {
    "type": "ROW", "id": row_id, "children": [],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"},
}
position[row_id]["children"].append("CHART-71")
position["CHART-71"] = {
    "type": "CHART", "id": "CHART-71", "children": [],
    "parents": ["ROOT_ID", "GRID_ID", row_id],
    "meta": {"chartId": 71, "width": 12, "height": 50, "sliceName": charts[71]},
}

# Row 2b: 2 donut charts
row_id = "ROW-2-1"
position["GRID_ID"]["children"].append(row_id)
position[row_id] = {
    "type": "ROW", "id": row_id, "children": [],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"},
}
for cid in [72, 73]:
    chart_key = f"CHART-{cid}"
    position[row_id]["children"].append(chart_key)
    position[chart_key] = {
        "type": "CHART", "id": chart_key, "children": [],
        "parents": ["ROOT_ID", "GRID_ID", row_id],
        "meta": {"chartId": cid, "width": 6, "height": 50, "sliceName": charts[cid]},
    }

# Section 3: Performa Akademik
# Row 1: Status Kelulusan (6w) + Persentase TW (6w) — DOMINANT
# Row 2: IPK (4w) + Lama Studi (4w) + ??? — wait, user also wants SKS
# User wants: IPK, SKS, Lama Studi, Persentase TW, Status Kelulusan = 5 charts
# But SKS chart (75) was removed. User said "Rata-rata SKS per Angkatan" in section 4
# Let me re-read: "C. Rata-rata SKS per Angkatan (Lulus)" — this is chart 75
# But chart 75 was in the "removed" list. Let me check if user wants it back.
# User says in section 4: "C. Rata-rata SKS per Angkatan (Lulus) - Bar chart."
# So yes, chart 75 should be included.

# Let me add chart 75 back
charts[75] = "Rata-rata Total SKS per Angkatan (Lulus)"

# Section 3: Performa Akademik
# Row 1: Status Kelulusan (6w) + Persentase TW (6w)
# Row 2: IPK (4w) + SKS (4w) + Lama Studi (4w)
add_section(3, "Performa Akademik", [
    [79, 80],
    [74, 75, 77],
])

# Section 4: Hasil Evaluasi Model
# Row 1: Confusion Matrix (7w) + Classification Report (5w)
add_section(4, "Hasil Evaluasi Model", [
    [85, 86],
])

# Section 5: Hasil Prediksi Mahasiswa Aktif
# Row 1: Prediksi per Angkatan (8w) + Distribusi (4w)
# Actually let me use 6w+6w for balance
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
chart_count = 0
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        chart_count += 1
        print(f"  Chart {meta.get('chartId')}: {meta.get('width')}w | {meta.get('sliceName')}")
print(f"\nTotal charts: {chart_count}")
