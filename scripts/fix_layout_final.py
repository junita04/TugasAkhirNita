"""
Fix remaining layout issues:
- Chart 78 (Status Kelulusan pie) width=12 -> should be smaller
- Chart 89 (Selisih SKS per Semester) width=12 -> should be smaller
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
        "meta": {"text": title, "headerFontColor": "#1FA8C9", "headerFontSize": 0.6},
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

# Section 1: Ringkasan Akademik - 4 KPIs + 1
add_section(1, "Ringkasan Akademik", [
    [66, 67, 68, 69],  # 4 KPIs at width=3
    [70],               # Terlambat at width=3
])

# Section 2: Profil Mahasiswa
add_section(2, "Profil Mahasiswa", [
    [71, 72, 73],  # Bar + 2 Pies at width=4
])

# Section 3: Profil Akademik
add_section(3, "Profil Akademik", [
    [74, 75, 76, 77],  # 4 bars at width=3
    [79, 80],           # Stacked bar + percentage at width=6
])

# Section 4: Hasil Evaluasi ML
add_section(4, "Hasil Evaluasi Machine Learning", [
    [81, 82, 83, 84],  # 4 KPIs at width=3
    [85, 86],           # Confusion Matrix + Classification Report at width=6
])

# Section 5: Hasil Prediksi
add_section(5, "Hasil Prediksi Mahasiswa Aktif", [
    [87, 88],      # Bar + Pie at width=6
    [78, 78],      # Wait, can't duplicate. Let me fix this
])

# Actually section 5: 3 charts
# Row 1: 87, 88 (width=6 each)
# Row 2: 78 (width=6, centered)
# But 1 chart at width=6 leaves empty space. Let me put it at width=12 or pair it.

# Rebuild section 5
# Remove old section 5 children
old_children = position["GRID_ID"]["children"]
position["GRID_ID"]["children"] = [c for c in old_children if not c.startswith("ROW-section-5") and not c.startswith("ROW-5-")]

# Section 5 row 1: 87, 88 (width=6)
row_id = "ROW-5-0"
position["GRID_ID"]["children"].append(row_id)
position[row_id] = {
    "type": "ROW", "id": row_id, "children": [],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"},
}
for cid in [87, 88]:
    chart_key = f"CHART-{cid}"
    position[row_id]["children"].append(chart_key)
    position[chart_key] = {
        "type": "CHART", "id": chart_key, "children": [],
        "parents": ["ROOT_ID", "GRID_ID", row_id],
        "meta": {"chartId": cid, "width": 6, "height": 50, "sliceName": charts[cid]},
    }

# Section 5 row 2: 78 at width=12 (full width pie for status kelulusan)
row_id = "ROW-5-1"
position["GRID_ID"]["children"].append(row_id)
position[row_id] = {
    "type": "ROW", "id": row_id, "children": [],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"},
}
chart_key = "CHART-78"
position[row_id]["children"].append(chart_key)
position[chart_key] = {
    "type": "CHART", "id": chart_key, "children": [],
    "parents": ["ROOT_ID", "GRID_ID", row_id],
    "meta": {"chartId": 78, "width": 12, "height": 50, "sliceName": charts[78]},
}

# Insert section 5 title
title_row_id = "ROW-section-5"
position["GRID_ID"]["children"].insert(
    position["GRID_ID"]["children"].index("ROW-5-0"), title_row_id)
position[title_row_id] = {
    "type": "ROW", "id": title_row_id, "children": [],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"},
}
title_id = "HEADER-5"
position[title_row_id]["children"].append(title_id)
position[title_id] = {
    "type": "HEADER", "id": title_id,
    "meta": {"text": "Hasil Prediksi Mahasiswa Aktif", "headerFontColor": "#1FA8C9", "headerFontSize": 0.6},
}

# Section 6: Analisis Mahasiswa Aktif
# Remove old section 6
old_children = position["GRID_ID"]["children"]
position["GRID_ID"]["children"] = [c for c in old_children if not c.startswith("ROW-section-6") and not c.startswith("ROW-6-")]

# Row 1: 100, 91 (width=6)
row_id = "ROW-6-0"
position["GRID_ID"]["children"].append(row_id)
position[row_id] = {
    "type": "ROW", "id": row_id, "children": [],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"},
}
for cid in [100, 91]:
    chart_key = f"CHART-{cid}"
    position[row_id]["children"].append(chart_key)
    position[chart_key] = {
        "type": "CHART", "id": chart_key, "children": [],
        "parents": ["ROOT_ID", "GRID_ID", row_id],
        "meta": {"chartId": cid, "width": 6, "height": 50, "sliceName": charts[cid]},
    }

# Row 2: 89 at width=12
row_id = "ROW-6-1"
position["GRID_ID"]["children"].append(row_id)
position[row_id] = {
    "type": "ROW", "id": row_id, "children": [],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"},
}
chart_key = "CHART-89"
position[row_id]["children"].append(chart_key)
position[chart_key] = {
    "type": "CHART", "id": chart_key, "children": [],
    "parents": ["ROOT_ID", "GRID_ID", row_id],
    "meta": {"chartId": 89, "width": 12, "height": 50, "sliceName": charts[89]},
}

# Insert section 6 title
title_row_id = "ROW-section-6"
position["GRID_ID"]["children"].insert(
    position["GRID_ID"]["children"].index("ROW-6-0"), title_row_id)
position[title_row_id] = {
    "type": "ROW", "id": title_row_id, "children": [],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"},
}
title_id = "HEADER-6"
position[title_row_id]["children"].append(title_id)
position[title_id] = {
    "type": "HEADER", "id": title_id,
    "meta": {"text": "Analisis Mahasiswa Aktif", "headerFontColor": "#1FA8C9", "headerFontSize": 0.6},
}

# Print final layout
print("Final GRID_ID children:")
for i, c in enumerate(position["GRID_ID"]["children"]):
    print(f"  {i}: {c}")

# Update
r = s.put(f"{BASE}/api/v1/dashboard/3", json={
    "position_json": json.dumps(position),
    "dashboard_title": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa",
})
print(f"\nDashboard updated: {r.status_code}")

# Verify chart widths
r2 = s.get(f"{BASE}/api/v1/dashboard/3")
pos = json.loads(r2.json()["result"]["position_json"])
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        print(f"  Chart {meta.get('chartId')}: {meta.get('height')}h x {meta.get('width')}w")
