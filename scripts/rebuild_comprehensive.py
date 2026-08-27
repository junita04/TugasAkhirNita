"""
COMPREHENSIVE DASHBOARD REBUILD - MAROON THEME
All charts + layout in one script
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

def make_metric(sql, label):
    return {"expressionType": "SQL", "sqlExpression": sql, "label": label}

def make_adhoc(subject, op, comp):
    return {"expressionType": "SIMPLE", "subject": subject, "operator": op, "comparator": comp, "clause": "WHERE"}

s = api()

# ============================================================
# STEP 1: FIX CHART 86 - Classification Report -> Bar Chart
# ============================================================
print("=" * 70)
print("STEP 1: Fix Classification Report -> Bar Chart")
print("=" * 70)

# Classification Report data:
# Tepat Waktu: precision=0.47, recall=0.65, f1=0.54
# Terlambat: precision=0.87, recall=0.77, f1=0.82
# weighted_avg: precision=0.78, recall=0.74, f1=0.75

# Create a grouped bar chart showing precision, recall, f1 for each class
cr_params = {
    "viz_type": "echarts_timeseries_bar",
    "x_axis": "class",
    "metrics": [
        make_metric("precision", "Precision"),
        make_metric("recall", "Recall"),
        make_metric("f1_score", "F1 Score"),
    ],
    "groupby": [],
    "row_limit": 10,
    "show_legend": True,
    "rich_tooltip": True,
    "stack": False,
    "color_scheme": "supersetCategory10",
    "adhoc_filters": [
        {"expressionType": "SIMPLE", "subject": "class", "operator": "!=", "comparator": "weighted_avg", "clause": "WHERE"}
    ],
}

cr_qc = {
    "datasource": {"id": 10, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [
            make_metric("precision", "Precision"),
            make_metric("recall", "Recall"),
            make_metric("f1_score", "F1 Score"),
        ],
        "columns": ["class"],
        "filters": [{"col": "class", "op": "!=", "val": "weighted_avg"}],
    }],
    "form_data": cr_params,
    "result_format": "json",
    "result_type": "full",
}

r = s.post(f"{BASE}/api/v1/chart/data", json=cr_qc)
if r.status_code == 200:
    data = r.json()
    rc = data["result"][0].get("rowcount", 0) if data.get("result") else 0
    print(f"Classification Report bar: OK ({rc} rows)")
else:
    print(f"Classification Report bar: FAIL ({r.status_code})")

s.put(f"{BASE}/api/v1/chart/86", json={
    "params": json.dumps(cr_params),
    "viz_type": "echarts_timeseries_bar",
    "query_context": json.dumps(cr_qc),
})

# ============================================================
# STEP 2: FIX CHART 85 - Confusion Matrix -> Better Table
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: Fix Confusion Matrix -> Styled Table")
print("=" * 70)

# The confusion matrix data is:
# actual=Tepat Waktu, predicted=Tepat Waktu, count=410  (TP)
# actual=Tepat Waktu, predicted=Terlambat, count=221    (FN)
# actual=Terlambat, predicted=Tepat Waktu, count=469    (FP)
# actual=Terlambat, predicted=Terlambat, count=1537     (TN)

# Keep as table but improve styling
cm_params = {
    "viz_type": "table",
    "all_columns": ["actual", "predicted", "count"],
    "metrics": [],
    "groupby": [],
    "order_desc": True,
    "row_limit": 10,
    "page_length": 10,
    "include_search": False,
    "show_cell_bars": True,
    "color_pn": True,
}

cm_qc = {
    "datasource": {"id": 9, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [],
        "columns": ["actual", "predicted", "count"],
        "filters": [],
    }],
    "form_data": cm_params,
    "result_format": "json",
    "result_type": "full",
}

s.put(f"{BASE}/api/v1/chart/85", json={
    "params": json.dumps(cm_params),
    "viz_type": "table",
    "query_context": json.dumps(cm_qc),
})
print("Confusion Matrix: updated")

# ============================================================
# STEP 3: FIX CHART 100 - IPK Distribution -> Histogram
# ============================================================
print("\n" + "=" * 70)
print("STEP 3: Fix IPK Distribution -> Histogram")
print("=" * 70)

# Check current state
r = s.get(f"{BASE}/api/v1/chart/100")
c = r.json()["result"]
current_viz = c["viz_type"]
print(f"Current viz_type: {current_viz}")

# Try histogram
hist_params = {
    "viz_type": "histogram",
    "all_columns_x": ["ipk"],
    "adhoc_filters": [make_adhoc("status_mahasiswa", "==", "AKTIF")],
    "row_limit": 10000,
    "groupby": [],
    "color_scheme": "supersetCategory10",
    "link_length": 25,
    "x_axis_label": "IPK",
    "y_axis_label": "Jumlah Mahasiswa",
    "normalize": False,
    "show_legend": False,
}

hist_qc = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10000,
        "metrics": [],
        "columns": ["ipk"],
        "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
    }],
    "form_data": hist_params,
    "result_format": "json",
    "result_type": "full",
}

r = s.post(f"{BASE}/api/v1/chart/data", json=hist_qc)
if r.status_code == 200:
    data = r.json()
    rc = data["result"][0].get("rowcount", 0) if data.get("result") else 0
    print(f"Histogram: OK ({rc} rows)")
    s.put(f"{BASE}/api/v1/chart/100", json={
        "params": json.dumps(hist_params),
        "viz_type": "histogram",
        "query_context": json.dumps(hist_qc),
    })
else:
    print(f"Histogram: FAIL ({r.status_code}), keeping current")

# ============================================================
# STEP 4: UPDATE ALL CHART COLORS
# ============================================================
print("\n" + "=" * 70)
print("STEP 4: Update All Chart Colors")
print("=" * 70)

COLOR_SCHEME = "supersetCategory10"

# Bar charts - update color scheme
bar_charts = [71, 74, 75, 76, 77, 79, 80, 87, 89, 91]
for cid in bar_charts:
    r = s.get(f"{BASE}/api/v1/chart/{cid}")
    c = r.json()["result"]
    params = json.loads(c["params"])
    params["color_scheme"] = COLOR_SCHEME
    params["show_legend"] = params.get("show_legend", False)
    params["rich_tooltip"] = True
    s.put(f"{BASE}/api/v1/chart/{cid}", json={"params": json.dumps(params)})
    print(f"Chart {cid}: updated colors")

# Pie charts - update color scheme
pie_charts = [72, 73, 78, 88]
for cid in pie_charts:
    r = s.get(f"{BASE}/api/v1/chart/{cid}")
    c = r.json()["result"]
    params = json.loads(c["params"])
    params["color_scheme"] = COLOR_SCHEME
    params["show_legend"] = True
    params["show_labels"] = True
    params["label_type"] = "key_value_percent"
    params["donut"] = True
    params["innerRadius"] = 40
    params["outerRadius"] = 80
    s.put(f"{BASE}/api/v1/chart/{cid}", json={"params": json.dumps(params)})
    print(f"Chart {cid}: updated colors")

# KPI charts - keep as is (big_number_total doesn't use color_scheme)

# ============================================================
# STEP 5: REBUILD DASHBOARD LAYOUT
# ============================================================
print("\n" + "=" * 70)
print("STEP 5: Rebuild Dashboard Layout")
print("=" * 70)

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

# Section 1: Ringkasan Akademik - 5 KPIs in TWO rows
# Row 1: 4 KPIs (3w each = 12)
# Row 2: 1 KPI (3w, left-aligned)
add_section(1, "Ringkasan Akademik", [
    [66, 67, 68, 69],
    [70],
])

# Section 2: Profil Mahasiswa - 3 charts in 1 row
add_section(2, "Profil Mahasiswa", [
    [71, 72, 73],
])

# Section 3: Profil Akademik - 2 rows
add_section(3, "Profil Akademik", [
    [74, 75, 76],
    [77, 79, 80],
])

# Section 4: Hasil Evaluasi ML - 2 rows
add_section(4, "Hasil Evaluasi Machine Learning", [
    [81, 82, 83, 84],
    [85, 86],
])

# Section 5: Hasil Prediksi - 2 rows
add_section(5, "Hasil Prediksi Mahasiswa Aktif", [
    [87, 88],
    [78],
])

# Section 6: Analisis Mahasiswa Aktif - 2 rows
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

# Verify
r2 = s.get(f"{BASE}/api/v1/dashboard/3")
pos = json.loads(r2.json()["result"]["position_json"])
chart_count = sum(1 for v in pos.values() if isinstance(v, dict) and v.get("type") == "CHART")
print(f"Charts in layout: {chart_count}")
