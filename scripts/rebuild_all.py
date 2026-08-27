"""
Comprehensive dashboard rebuild:
1. Fix all chart params for proper rendering
2. Fix layout with proper sizing and spacing
3. Apply professional color scheme
4. Fix Confusion Matrix and IPK Distribution
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

def make_simple_metric(metric_name):
    return {"expressionType": "SIMPLE", "column": {"column_name": metric_name}, "label": metric_name}

def make_adhoc(subject, op, comp):
    return {"expressionType": "SIMPLE", "subject": subject, "operator": op, "comparator": comp, "clause": "WHERE"}

def convert_adhoc(f):
    return {"col": f["subject"], "op": f["operator"], "val": f["comparator"]}

s = api()

# ============================================================
# STEP 1: FIX CHART PARAMS
# ============================================================
print("=" * 70)
print("STEP 1: FIXING CHART PARAMS")
print("=" * 70)

# --- Chart 70: Terlambat - fix width (was 12, should be 3) ---
# Will be fixed in layout rebuild

# --- Chart 85: Confusion Matrix ---
# Already a table with actual, predicted, count - working fine
# Just ensure show_cell_bars is on for visual color
r = s.get(f"{BASE}/api/v1/chart/85")
c85 = r.json()["result"]
params85 = json.loads(c85["params"])
params85["show_cell_bars"] = True
params85["page_length"] = 10
s.put(f"{BASE}/api/v1/chart/85", json={"params": json.dumps(params85)})
print("Chart 85 (Confusion Matrix): updated params")

# --- Chart 100: Distribusi IPK - convert to bar chart ---
# Use bar chart with IPK as x_axis for visual distribution
print("\nConverting Chart 100 to bar chart...")
params100 = {
    "viz_type": "echarts_timeseries_bar",
    "x_axis": "ipk",
    "time_grain_sqla": "P1D",
    "metrics": [make_metric("COUNT(*)", "Jumlah Mahasiswa")],
    "groupby": [],
    "order_desc": True,
    "row_limit": 500,
    "truncate_metric": True,
    "show_legend": False,
    "rich_tooltip": True,
    "tooltipTimeFormat": "smart_date",
    "x_axis_time_format": "smart_date",
    "stack": False,
    "show_bar_value": False,
    "bar_stacked": False,
    "row_limit_viz": 500,
    "adhoc_filters": [make_adhoc("status_mahasiswa", "==", "AKTIF")],
    "color_scheme": "supersetCategory10",
}

# Update chart
s.put(f"{BASE}/api/v1/chart/100", json={
    "params": json.dumps(params100),
    "viz_type": "echarts_timeseries_bar",
})

# Build query_context
qc100 = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 500,
        "metrics": [make_metric("COUNT(*)", "Jumlah Mahasiswa")],
        "columns": [],
        "orderby": [["COUNT(*)", False]],
        "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
    }],
    "form_data": params100,
    "result_format": "json",
    "result_type": "full",
}
s.put(f"{BASE}/api/v1/chart/100", json={"query_context": json.dumps(qc100)})

# Test
r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc100)
if r2.status_code == 200:
    data = r2.json()
    rc = data["result"][0].get("rowcount", 0) if data.get("result") else 0
    print(f"Chart 100: OK ({rc} rows)")
else:
    print(f"Chart 100: FAIL ({r2.status_code})")
    # Fallback to table
    print("Falling back to table chart...")
    params100_fb = {
        "viz_type": "table",
        "all_columns": [],
        "metrics": [make_metric("COUNT(*)", "Jumlah")],
        "groupby": ["ipk"],
        "order_desc": True,
        "row_limit": 500,
        "page_length": 25,
        "include_search": True,
        "show_cell_bars": True,
        "adhoc_filters": [make_adhoc("status_mahasiswa", "==", "AKTIF")],
    }
    s.put(f"{BASE}/api/v1/chart/100", json={
        "params": json.dumps(params100_fb),
        "viz_type": "table",
    })
    qc_fb = {
        "datasource": {"id": 5, "type": "table"},
        "queries": [{
            "time_range": "No filter",
            "granularity_sqla": None,
            "row_limit": 500,
            "metrics": [make_metric("COUNT(*)", "Jumlah")],
            "columns": ["ipk"],
            "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
        }],
        "form_data": params100_fb,
        "result_format": "json",
        "result_type": "full",
    }
    s.put(f"{BASE}/api/v1/chart/100", json={"query_context": json.dumps(qc_fb)})
    r3 = s.post(f"{BASE}/api/v1/chart/data", json=qc_fb)
    if r3.status_code == 200:
        data = r3.json()
        rc = data["result"][0].get("rowcount", 0) if data.get("result") else 0
        print(f"Chart 100 fallback: OK ({rc} rows)")
    else:
        print(f"Chart 100 fallback: FAIL ({r3.status_code})")

# ============================================================
# STEP 2: REBUILD DASHBOARD LAYOUT
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: REBUILDING DASHBOARD LAYOUT")
print("=" * 70)

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

# Colors
BLUE = "#2563EB"
CYAN = "#06B6D4"
GREEN = "#10B981"
ORANGE = "#F59E0B"
RED = "#EF4444"
PURPLE = "#8B5CF6"

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

def add_section(section_idx, title, chart_rows, section_height=0):
    """
    chart_rows: list of lists, each inner list is [chart_id, ...] for one row
    """
    # Section title
    title_row_id = f"ROW-section-{section_idx}"
    position["GRID_ID"]["children"].append(title_row_id)
    position[title_row_id] = {
        "type": "ROW",
        "id": title_row_id,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID"],
        "meta": {"background": "BACKGROUND_TRANSPARENT"},
    }
    title_id = f"HEADER-{section_idx}"
    position[title_row_id]["children"].append(title_id)
    position[title_id] = {
        "type": "HEADER",
        "id": title_id,
        "meta": {"text": title, "headerFontColor": "#1FA8C9", "headerFontSize": 0.6},
    }

    for row_idx, row_charts in enumerate(chart_rows):
        row_id = f"ROW-{section_idx}-{row_idx}"
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
                    "height": 50,
                    "sliceName": charts.get(cid, f"Chart {cid}"),
                },
            }

# Section 1: Ringkasan Akademik - 5 KPI cards in one row
add_section(1, "Ringkasan Akademik", [
    [66, 67, 68, 69, 70]  # 5 KPIs, each width=2 (12/5 not even, use 3+3+3+3 for 4, last one gets rest)
])

# Section 2: Profil Mahasiswa - 2 rows
add_section(2, "Profil Mahasiswa", [
    [71, 72, 73]  # Bar + 2 Pies
])

# Section 3: Profil Akademik - 2 rows of 3
add_section(3, "Profil Akademik", [
    [74, 75, 76],
    [77, 79, 80],
])

# Section 4: Evaluasi ML - 2 rows
add_section(4, "Hasil Evaluasi Machine Learning", [
    [81, 82, 83, 84],       # 4 KPI metrics
    [85, 86],                # Confusion Matrix + Classification Report
])

# Section 5: Hasil Prediksi - 2 rows
add_section(5, "Hasil Prediksi Mahasiswa Aktif", [
    [87, 88],                # Bar + Pie
    [78],                     # Status Kelulusan pie
])

# Section 6: Analisis Mahasiswa Aktif - 2 rows
add_section(6, "Analisis Mahasiswa Aktif", [
    [100, 91],               # IPK Distribution + Mahasiswa Aktif per Semester
    [89],                     # Selisih SKS per Semester
])

# Fix: KPI row should be 5 items, widths don't divide evenly into 12
# Let's use width=2 for first 4 and width=4 for last, or use nested columns
# Actually, Superset uses width/12 ratio. 5 items at width=2 = 10, need 12.
# Let's put 4 KPIs in one row and 1 in the next, or use width=3 for 4 items (total 12)
# Better: put all 5 KPIs in one row with widths [3, 3, 3, 3, 3] = 15, which is >12
# Solution: Put 4 KPIs in row 1, 1 KPI + spacer in row 2

# Actually let me rebuild section 1 properly
# Remove old section 1 children from GRID
old_children = position["GRID_ID"]["children"]
position["GRID_ID"]["children"] = [c for c in old_children if not c.startswith("ROW-section-1") and not c.startswith("ROW-1-")]

# Rebuild section 1 with two rows
# Row 1: 4 KPIs
row1_id = "ROW-1-0"
position["GRID_ID"]["children"].insert(0, row1_id)
position[row1_id] = {
    "type": "ROW",
    "id": row1_id,
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"},
}
for cid in [66, 67, 68, 69]:
    chart_key = f"CHART-{cid}"
    position[row1_id]["children"].append(chart_key)
    position[chart_key] = {
        "type": "CHART",
        "id": chart_key,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", row1_id],
        "meta": {
            "chartId": cid,
            "width": 3,
            "height": 50,
            "sliceName": charts[cid],
        },
    }

# Row 2: Terlambat + 3 spacers (or just Terlambat at width 3)
row2_id = "ROW-1-1"
position["GRID_ID"]["children"].insert(1, row2_id)
position[row2_id] = {
    "type": "ROW",
    "id": row2_id,
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"},
}
chart_key = "CHART-70"
position[row2_id]["children"].append(chart_key)
position[chart_key] = {
    "type": "CHART",
    "id": chart_key,
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID", row2_id],
    "meta": {
        "chartId": 70,
        "width": 3,
        "height": 50,
        "sliceName": charts[70],
    },
}

# Make sure section title is first
title_row_id = "ROW-section-1"
if title_row_id in position["GRID_ID"]["children"]:
    position["GRID_ID"]["children"].remove(title_row_id)
position["GRID_ID"]["children"].insert(0, title_row_id)

# Verify order
print("GRID_ID children order:")
for i, c in enumerate(position["GRID_ID"]["children"]):
    print(f"  {i}: {c}")

# Update dashboard
r = s.put(f"{BASE}/api/v1/dashboard/3", json={
    "position_json": json.dumps(position),
    "dashboard_title": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa",
})
print(f"\nDashboard updated: {r.status_code}")

# ============================================================
# STEP 3: VALIDATE
# ============================================================
print("\n" + "=" * 70)
print("STEP 3: VALIDATION")
print("=" * 70)

r2 = s.get(f"{BASE}/api/v1/dashboard/3")
dash = r2.json()["result"]
pos = json.loads(dash.get("position_json", "{}"))

chart_refs = set()
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        chart_id = meta.get("chartId")
        height = meta.get("height", "?")
        width = meta.get("width", "?")
        if chart_id:
            chart_refs.add(chart_id)
            r1 = s.get(f"{BASE}/api/v1/chart/{cid}")
            status = "OK" if r1.status_code == 200 else "FAIL"

print(f"Charts in layout: {len(chart_refs)}")
print(f"Chart IDs: {sorted(chart_refs)}")

# Validate each chart
ok = 0
fail = 0
for cid in sorted(chart_refs):
    r1 = s.get(f"{BASE}/api/v1/chart/{cid}")
    if r1.status_code != 200:
        print(f"Chart {cid}: NOT FOUND")
        fail += 1
        continue
    c = r1.json()["result"]
    qc_str = c.get("query_context")
    if not qc_str:
        print(f"Chart {cid}: NO QC")
        fail += 1
        continue
    qc = json.loads(qc_str)
    r3 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
    if r3.status_code == 200:
        data = r3.json()
        rc = data["result"][0].get("rowcount", 0) if data.get("result") else 0
        print(f"Chart {cid:4d}: OK | {rc:>5} rows | {c['viz_type']:25s} | {c['slice_name']}")
        ok += 1
    else:
        print(f"Chart {cid:4d}: FAIL | {c['viz_type']:25s} | {c['slice_name']}")
        fail += 1

print(f"\nVALID: {ok}/{ok+fail}")
print(f"BROKEN: {fail}")
