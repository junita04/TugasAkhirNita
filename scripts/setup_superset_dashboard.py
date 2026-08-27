"""
Superset Dashboard Setup Script
===============================
Creates datasets, charts, and dashboard for the thesis project.
All data comes from Iceberg gold tables via Trino.
"""

import json
import requests
import time

BASE_URL = "http://localhost:8088"
session = requests.Session()

# ============================================================
# LOGIN
# ============================================================
def login():
    r = session.post(f"{BASE_URL}/api/v1/security/login",
                     json={"username": "admin", "password": "change-me", "provider": "db"})
    token = r.json().get("access_token", "")
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    # Get CSRF token
    r0 = session.get(f"{BASE_URL}/api/v1/security/csrf_token/")
    csrf = r0.json().get("result", "")
    session.headers.update({
        "X-CSRFToken": csrf,
        "Referer": BASE_URL,
    })
    print(f"Login: OK (token={token[:20]}...)")

# ============================================================
# DATASETS
# ============================================================
def get_existing_datasets():
    r = session.get(f"{BASE_URL}/api/v1/dataset/?q=(page_size:200)")
    data = r.json()
    return {d["table_name"]: d["id"] for d in data.get("result", [])}

def register_dataset(schema, table_name):
    r = session.post(f"{BASE_URL}/api/v1/dataset/", json={
        "database": 1,
        "schema": schema,
        "table_name": table_name,
    })
    if r.status_code in (200, 201):
        ds_id = r.json().get("id")
        print(f"  Registered: {schema}.{table_name} (id={ds_id})")
        return ds_id
    elif r.status_code == 422:
        # Already exists, find it
        existing = get_existing_datasets()
        if table_name in existing:
            print(f"  Already exists: {schema}.{table_name} (id={existing[table_name]})")
            return existing[table_name]
    print(f"  Error registering {schema}.{table_name}: {r.status_code} {r.text[:200]}")
    return None

def ensure_datasets():
    print("\n=== DATASETS ===")
    ds = {}
    gold_tables = [
        "data_referensi_mahasiswa",
        "model_metrics",
        "confusion_matrix",
        "classification_report",
        "prediction_by_angkatan",
        "model_predictions",
    ]
    for t in gold_tables:
        ds[t] = register_dataset("gold", t)
    return ds

# ============================================================
# CHART HELPERS
# ============================================================
chart_id_counter = [100]

def create_chart(dataset_id, viz_type, params, slice_name, datasource_id=None):
    """Create a chart via Superset API"""
    payload = {
        "slice_name": slice_name,
        "viz_type": viz_type,
        "datasource_id": dataset_id or datasource_id,
        "datasource_type": "table",
        "params": json.dumps(params),
    }
    r = session.post(f"{BASE_URL}/api/v1/chart/", json=payload)
    if r.status_code in (200, 201):
        cid = r.json().get("id")
        print(f"  Chart created: {slice_name} (id={cid})")
        return cid
    else:
        print(f"  Error creating chart '{slice_name}': {r.status_code}")
        print(f"    {r.text[:300]}")
        return None

# ============================================================
# KPI CHARTS (Section 1)
# ============================================================
def create_kpi_charts(ds):
    print("\n=== SECTION 1: KPI CHARTS ===")
    charts = []
    
    # KPI 1: Total Mahasiswa
    cid = create_chart(ds["data_referensi_mahasiswa"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total Mahasiswa"},
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
        "y_axis_format": "SMART_NUMBER",
    }, "Total Mahasiswa")
    if cid: charts.append(cid)

    # KPI 2: Mahasiswa Aktif
    cid = create_chart(ds["data_referensi_mahasiswa"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Mahasiswa Aktif"},
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}],
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
        "y_axis_format": "SMART_NUMBER",
    }, "Mahasiswa Aktif")
    if cid: charts.append(cid)

    # KPI 3: Mahasiswa Lulus
    cid = create_chart(ds["data_referensi_mahasiswa"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Mahasiswa Lulus"},
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "Lulus", "clause": "WHERE"}],
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
        "y_axis_format": "SMART_NUMBER",
    }, "Mahasiswa Lulus")
    if cid: charts.append(cid)

    # KPI 4: Tepat Waktu (from Gold status_kelulusan)
    cid = create_chart(ds["data_referensi_mahasiswa"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Tepat Waktu"},
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_kelulusan", "operator": "==", "comparator": "Tepat Waktu", "clause": "WHERE"}],
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
        "y_axis_format": "SMART_NUMBER",
    }, "Tepat Waktu (Aktual)")
    if cid: charts.append(cid)

    # KPI 5: Terlambat
    cid = create_chart(ds["data_referensi_mahasiswa"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Terlambat"},
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_kelulusan", "operator": "==", "comparator": "Terlambat", "clause": "WHERE"}],
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
        "y_axis_format": "SMART_NUMBER",
    }, "Terlambat (Aktual)")
    if cid: charts.append(cid)

    return charts

# ============================================================
# SECTION 2: PROFIL MAHASISWA
# ============================================================
def create_profil_charts(ds):
    print("\n=== SECTION 2: PROFIL MAHASISWA ===")
    charts = []

    # Chart: Jumlah Mahasiswa per Angkatan
    cid = create_chart(ds["data_referensi_mahasiswa"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah Mahasiswa"}],
        "groupby": [],
        "row_limit": 50,
        "truncate_metric": True,
        "show_legend": False,
        "rich_tooltip": True,
        "tooltipTimeFormat": "smart_date",
        "x_axis_title": "Angkatan",
        "y_axis_title": "Jumlah Mahasiswa",
        "y_axis_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
    }, "Jumlah Mahasiswa per Angkatan")
    if cid: charts.append(cid)

    # Chart: Distribusi Jenis Kelamin
    cid = create_chart(ds["data_referensi_mahasiswa"], "pie", {
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "groupby": ["jenis_kelamin"],
        "row_limit": 10,
        "show_labels": True,
        "labelsOutside": True,
        "label_type": "key_value_percent",
        "number_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
        "donut": True,
        "innerRadius": 50,
        "outerRadius": 80,
    }, "Distribusi Jenis Kelamin")
    if cid: charts.append(cid)

    # Chart: Distribusi Status Mahasiswa
    cid = create_chart(ds["data_referensi_mahasiswa"], "pie", {
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "groupby": ["status_mahasiswa"],
        "row_limit": 10,
        "show_labels": True,
        "label_type": "key_value_percent",
        "number_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
        "donut": True,
        "innerRadius": 50,
        "outerRadius": 80,
    }, "Distribusi Status Mahasiswa")
    if cid: charts.append(cid)

    return charts

# ============================================================
# SECTION 3: PERKEMBANGAN AKADEMIK
# ============================================================
def create_akademik_charts(ds):
    print("\n=== SECTION 3: PERKEMBANGAN AKADEMIK ===")
    charts = []

    # Chart: Rata-rata IPK per Angkatan (Lulus)
    cid = create_chart(ds["data_referensi_mahasiswa"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ipk), 2)", "label": "Rata-rata IPK"}],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "Lulus", "clause": "WHERE"}],
        "row_limit": 50,
        "show_legend": False,
        "rich_tooltip": True,
        "x_axis_title": "Angkatan",
        "y_axis_title": "Rata-rata IPK",
        "y_axis_format": ",.2f",
        "color_scheme": "supersetColors",
    }, "Rata-rata IPK per Angkatan (Lulus)")
    if cid: charts.append(cid)

    # Chart: Rata-rata Total SKS per Angkatan (Lulus)
    cid = create_chart(ds["data_referensi_mahasiswa"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(total_sks), 1)", "label": "Rata-rata Total SKS"}],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "Lulus", "clause": "WHERE"}],
        "row_limit": 50,
        "show_legend": False,
        "rich_tooltip": True,
        "x_axis_title": "Angkatan",
        "y_axis_title": "Rata-rata Total SKS",
        "y_axis_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
    }, "Rata-rata Total SKS per Angkatan (Lulus)")
    if cid: charts.append(cid)

    # Chart: Rata-rata Selisih SKS per Angkatan (Lulus)
    cid = create_chart(ds["data_referensi_mahasiswa"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(selisih_sks), 1)", "label": "Rata-rata Selisih SKS"}],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "Lulus", "clause": "WHERE"}],
        "row_limit": 50,
        "show_legend": False,
        "rich_tooltip": True,
        "x_axis_title": "Angkatan",
        "y_axis_title": "Rata-rata Selisih SKS",
        "y_axis_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
    }, "Rata-rata Selisih SKS per Angkatan (Lulus)")
    if cid: charts.append(cid)

    # Chart: Rata-rata Lama Studi per Angkatan (Lulus)
    cid = create_chart(ds["data_referensi_mahasiswa"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(lama_studi), 2)", "label": "Rata-rata Lama Studi (tahun)"}],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "Lulus", "clause": "WHERE"}],
        "row_limit": 50,
        "show_legend": False,
        "rich_tooltip": True,
        "x_axis_title": "Angkatan",
        "y_axis_title": "Tahun",
        "y_axis_format": ",.1f",
        "color_scheme": "supersetColors",
    }, "Rata-rata Lama Studi per Angkatan (Lulus)")
    if cid: charts.append(cid)

    return charts

# ============================================================
# SECTION 4: STATUS KELULUSAN
# ============================================================
def create_kelulusan_charts(ds):
    print("\n=== SECTION 4: STATUS KELULUSAN ===")
    charts = []

    # Chart: Donut Tepat Waktu vs Terlambat (Aktual)
    cid = create_chart(ds["data_referensi_mahasiswa"], "pie", {
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "groupby": ["status_kelulusan"],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "Lulus", "clause": "WHERE"}],
        "row_limit": 10,
        "show_labels": True,
        "label_type": "key_value_percent",
        "number_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
        "donut": True,
        "innerRadius": 50,
        "outerRadius": 80,
    }, "Status Kelulusan Aktual (Tepat Waktu vs Terlambat)")
    if cid: charts.append(cid)

    # Chart: Status Kelulusan per Angkatan (Stacked Bar)
    cid = create_chart(ds["data_referensi_mahasiswa"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "groupby": ["status_kelulusan"],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "Lulus", "clause": "WHERE"}],
        "row_limit": 50,
        "show_legend": True,
        "rich_tooltip": True,
        "stack": True,
        "x_axis_title": "Angkatan",
        "y_axis_title": "Jumlah Mahasiswa",
        "y_axis_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
    }, "Status Kelulusan per Angkatan (Stacked)")
    if cid: charts.append(cid)

    # Chart: Persentase Tepat Waktu per Angkatan
    cid = create_chart(ds["data_referensi_mahasiswa"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(COUNT(CASE WHEN status_kelulusan='Tepat Waktu' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2)", "label": "Persentase Tepat Waktu (%)"}],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "Lulus", "clause": "WHERE"}],
        "row_limit": 50,
        "show_legend": False,
        "rich_tooltip": True,
        "x_axis_title": "Angkatan",
        "y_axis_title": "Persentase (%)",
        "y_axis_format": ",.1f",
        "color_scheme": "supersetColors",
    }, "Persentase Tepat Waktu per Angkatan")
    if cid: charts.append(cid)

    return charts

# ============================================================
# SECTION 5: HASIL PREDIKSI ML
# ============================================================
def create_ml_charts(ds):
    print("\n=== SECTION 5: HASIL PREDIKSI ML ===")
    charts = []

    # KPI: Accuracy
    cid = create_chart(ds["model_metrics"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(test_accuracy * 100, 2)", "label": "Accuracy (%)"},
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
        "y_axis_format": ",.2f",
    }, "Model Accuracy (%)")
    if cid: charts.append(cid)

    # KPI: F1 Score
    cid = create_chart(ds["model_metrics"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(test_f1 * 100, 2)", "label": "F1 Score (%)"},
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
        "y_axis_format": ",.2f",
    }, "Model F1 Score (%)")
    if cid: charts.append(cid)

    # KPI: Precision
    cid = create_chart(ds["model_metrics"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(test_precision * 100, 2)", "label": "Precision (%)"},
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
        "y_axis_format": ",.2f",
    }, "Model Precision (%)")
    if cid: charts.append(cid)

    # KPI: Recall
    cid = create_chart(ds["model_metrics"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(test_recall * 100, 2)", "label": "Recall (%)"},
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
        "y_axis_format": ",.2f",
    }, "Model Recall (%)")
    if cid: charts.append(cid)

    # Chart: Confusion Matrix as Heatmap
    cid = create_chart(ds["confusion_matrix"], "heatmap", {
        "all_columns_x": "actual",
        "all_columns_y": "predicted",
        "metric": {"expressionType": "SQL", "sqlExpression": "count", "label": "Jumlah"},
        "linear_color_scheme": "superset_seq_1",
        "show_legend": True,
        "show_values": True,
        "xscale_interval": None,
        "yscale_interval": None,
        "normalize_across": "x",
    }, "Confusion Matrix")
    if cid: charts.append(cid)

    # Chart: Classification Report Table
    cid = create_chart(ds["classification_report"], "table", {
        "all_columns": ["class", "precision", "recall", "f1_score", "support"],
        "order_desc": True,
        "row_limit": 10,
        "page_length": 10,
        "include_search": False,
        "table_timestamp_format": "smart_date",
        "show_cell_bars": True,
        "color_pn": True,
    }, "Classification Report")
    if cid: charts.append(cid)

    # Chart: Prediksi per Angkatan (from ML predictions)
    cid = create_chart(ds["prediction_by_angkatan"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [
            {"expressionType": "SQL", "sqlExpression": "prediksi_tepat_waktu", "label": "Prediksi Tepat Waktu"},
            {"expressionType": "SQL", "sqlExpression": "prediksi_terlambat", "label": "Prediksi Terlambat"},
        ],
        "groupby": [],
        "row_limit": 50,
        "show_legend": True,
        "rich_tooltip": True,
        "stack": False,
        "x_axis_title": "Angkatan",
        "y_axis_title": "Jumlah Mahasiswa",
        "y_axis_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
    }, "Prediksi ML per Angkatan (Aktif)")
    if cid: charts.append(cid)

    # Chart: Donut Prediksi ML
    cid = create_chart(ds["model_predictions"], "pie", {
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "groupby": ["prediksi"],
        "row_limit": 10,
        "show_labels": True,
        "label_type": "key_value_percent",
        "number_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
        "donut": True,
        "innerRadius": 50,
        "outerRadius": 80,
    }, "Distribusi Prediksi ML (Mahasiswa Aktif)")
    if cid: charts.append(cid)

    return charts

# ============================================================
# SECTION 6: MAHASISWA PERLU DIPERHATIKAN
# ============================================================
def create_attention_charts(ds):
    print("\n=== SECTION 6: PERHATIAN ===")
    charts = []

    # Chart: Distribusi Selisih SKS per Semester (from Gold)
    cid = create_chart(ds["data_referensi_mahasiswa"], "echarts_bar", {
        "x_axis": "semester",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(selisih_sks), 1)", "label": "Rata-rata Selisih SKS"}],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}],
        "row_limit": 50,
        "show_legend": False,
        "rich_tooltip": True,
        "x_axis_title": "Semester",
        "y_axis_title": "Rata-rata Selisih SKS",
        "y_axis_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
    }, "Rata-rata Selisih SKS per Semester (Aktif)")
    if cid: charts.append(cid)

    # Chart: Distribusi IPK Mahasiswa Aktif
    cid = create_chart(ds["data_referensi_mahasiswa"], "histogram", {
        "all_columns_x": ["ipk"],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}],
        "row_limit": 50000,
        "link_length": 25,
        "x_axis_label": "IPK",
        "y_axis_label": "Jumlah Mahasiswa",
        "color_scheme": "supersetColors",
        "normalized": False,
    }, "Distribusi IPK Mahasiswa Aktif")
    if cid: charts.append(cid)

    # Chart: Mahasiswa Aktif per Semester
    cid = create_chart(ds["data_referensi_mahasiswa"], "echarts_bar", {
        "x_axis": "semester",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah Mahasiswa"}],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}],
        "row_limit": 50,
        "show_legend": False,
        "rich_tooltip": True,
        "x_axis_title": "Semester",
        "y_axis_title": "Jumlah Mahasiswa",
        "y_axis_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
    }, "Jumlah Mahasiswa Aktif per Semester")
    if cid: charts.append(cid)

    return charts

# ============================================================
# DASHBOARD
# ============================================================
def create_dashboard(chart_ids, kpi_ids):
    print("\n=== CREATING DASHBOARD ===")

    # Build position_json
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
        "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID", "meta": {"text": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa"}},
    }

    row_id = 0
    chart_idx = 0

    def add_header(text):
        nonlocal row_id
        row_id += 1
        row_key = f"ROW-header-{row_id}"
        position[row_key] = {
            "type": "ROW", "id": row_key,
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"text": text, "background": "BACKGROUND_TRANSPARENT"},
        }
        position["GRID_ID"]["children"].append(row_key)
        return row_key

    def add_row():
        nonlocal row_id
        row_id += 1
        row_key = f"ROW-{row_id}"
        position[row_key] = {
            "type": "ROW", "id": row_key,
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        position["GRID_ID"]["children"].append(row_key)
        return row_key

    def add_chart(chart_id, parent_row, width=6, height=50):
        nonlocal chart_idx
        chart_idx += 1
        chart_key = f"CHART-{chart_idx}"
        position[chart_key] = {
            "type": "CHART", "id": chart_key,
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID", parent_row],
            "meta": {"width": width, "height": height, "chartId": chart_id, "sliceName": f"Chart {chart_idx}"},
        }
        position[parent_row]["children"].append(chart_key)
        return chart_key

    def add_kpi_row(kpi_ids_list):
        row = add_row()
        width = max(1, 12 // len(kpi_ids_list))
        for kid in kpi_ids_list:
            add_chart(kid, row, width=width, height=20)
        return row

    # HEADER
    add_header("Dashboard Prediksi Tingkat Kelulusan Mahasiswa")

    # SECTION 1: KPI
    add_header("Ringkasan Akademik")
    add_kpi_row(kpi_ids)

    # SECTION 2: Profil
    add_header("Profil Mahasiswa")
    r = add_row()
    add_chart(chart_ids["profil"][0], r, width=8, height=50)  # Angkatan bar
    add_chart(chart_ids["profil"][1], r, width=4, height=50)  # JK donut
    r2 = add_row()
    add_chart(chart_ids["profil"][2], r2, width=12, height=50)  # Status donut

    # SECTION 3: Perkembangan Akademik
    add_header("Perkembangan Akademik")
    r = add_row()
    add_chart(chart_ids["akademik"][0], r, width=6, height=50)  # IPK
    add_chart(chart_ids["akademik"][1], r, width=6, height=50)  # SKS
    r2 = add_row()
    add_chart(chart_ids["akademik"][2], r2, width=6, height=50)  # Selisih SKS
    add_chart(chart_ids["akademik"][3], r2, width=6, height=50)  # Lama Studi

    # SECTION 4: Status Kelulusan
    add_header("Status Kelulusan")
    r = add_row()
    add_chart(chart_ids["kelulusan"][0], r, width=4, height=50)  # Donut
    add_chart(chart_ids["kelulusan"][1], r, width=8, height=50)  # Stacked bar
    r2 = add_row()
    add_chart(chart_ids["kelulusan"][2], r2, width=12, height=50)  # Persentase

    # SECTION 5: Hasil Prediksi ML
    add_header("Hasil Prediksi Machine Learning")
    r = add_row()
    for kid in chart_ids["ml_kpi"]:
        add_chart(kid, r, width=3, height=20)
    r2 = add_row()
    add_chart(chart_ids["ml"][0], r2, width=6, height=50)  # Confusion Matrix
    add_chart(chart_ids["ml"][1], r2, width=6, height=50)  # Classification Report
    r3 = add_row()
    add_chart(chart_ids["ml"][2], r3, width=6, height=50)  # Prediksi per Angkatan
    add_chart(chart_ids["ml"][3], r3, width=6, height=50)  # Donut Prediksi

    # SECTION 6: Perhatian
    add_header("Analisis Mahasiswa Aktif")
    r = add_row()
    add_chart(chart_ids["attention"][0], r, width=4, height=50)  # Selisih SKS per semester
    add_chart(chart_ids["attention"][1], r, width=4, height=50)  # IPK histogram
    add_chart(chart_ids["attention"][2], r, width=4, height=50)  # Mahasiswa per semester

    # Create dashboard
    payload = {
        "dashboard_title": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa",
        "slug": "dashboard-prediksi-kelulusan",
        "published": True,
        "position_json": json.dumps(position),
    }
    r = session.post(f"{BASE_URL}/api/v1/dashboard/", json=payload)
    if r.status_code in (200, 201):
        dash_id = r.json().get("id")
        print(f"  Dashboard created: id={dash_id}")
        return dash_id
    else:
        print(f"  Error creating dashboard: {r.status_code}")
        print(f"    {r.text[:300]}")
        return None

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("SUPERSET DASHBOARD SETUP")
    print("=" * 70)
    
    login()
    ds = ensure_datasets()
    
    # Create all charts
    kpi_charts = create_kpi_charts(ds)
    profil_charts = create_profil_charts(ds)
    akademik_charts = create_akademik_charts(ds)
    kelulusan_charts = create_kelulusan_charts(ds)
    ml_charts = create_ml_charts(ds)
    attention_charts = create_attention_charts(ds)
    
    # Separate KPI from ML charts
    ml_kpi_charts = ml_charts[:4]
    ml_other_charts = ml_charts[4:]
    
    chart_ids = {
        "kpi": kpi_charts,
        "profil": profil_charts,
        "akademik": akademik_charts,
        "kelulusan": kelulusan_charts,
        "ml_kpi": ml_kpi_charts,
        "ml": ml_other_charts,
        "attention": attention_charts,
    }
    
    # Create dashboard
    dash_id = create_dashboard(chart_ids, kpi_charts)
    
    print()
    print("=" * 70)
    print("SETUP COMPLETE")
    print("=" * 70)
    if dash_id:
        print(f"Dashboard URL: http://localhost:8088/superset/dashboard/{dash_id}/")
    print(f"Datasets: {len(ds)}")
    print(f"Charts: KPI={len(kpi_charts)}, Profil={len(profil_charts)}, "
          f"Akademik={len(akademik_charts)}, Kelulusan={len(kelulusan_charts)}, "
          f"ML={len(ml_charts)}, Attention={len(attention_charts)}")
    total = len(kpi_charts) + len(profil_charts) + len(akademik_charts) + len(kelulusan_charts) + len(ml_charts) + len(attention_charts)
    print(f"Total charts: {total}")

if __name__ == "__main__":
    main()
