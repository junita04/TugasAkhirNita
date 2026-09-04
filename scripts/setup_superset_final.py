"""
Superset Dashboard Setup - Final Version
=========================================
Creates datasets, charts, and dashboard for the thesis project.
All data comes from Iceberg gold tables via Trino.
"""
import json
import requests
import time

BASE_URL = "http://academic-datalakehouse-superset-1:8088"
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
    r0 = session.get(f"{BASE_URL}/api/v1/security/csrf_token/")
    csrf = r0.json().get("result", "")
    session.headers.update({"X-CSRFToken": csrf, "Referer": BASE_URL})
    print(f"Login: OK")

# ============================================================
# DATASETS
# ============================================================
def get_existing_datasets():
    r = session.get(f"{BASE_URL}/api/v1/dataset/?q=(page_size:200)")
    data = r.json()
    return {d["table_name"]: d["id"] for d in data.get("result", [])}

def register_dataset(schema, table_name):
    r = session.post(f"{BASE_URL}/api/v1/dataset/", json={
        "database": 1, "schema": schema, "table_name": table_name,
    })
    if r.status_code in (200, 201):
        ds_id = r.json().get("id")
        print(f"  Created: {schema}.{table_name} (id={ds_id})")
        return ds_id
    elif r.status_code == 422:
        existing = get_existing_datasets()
        if table_name in existing:
            print(f"  Exists: {schema}.{table_name} (id={existing[table_name]})")
            return existing[table_name]
    print(f"  Error: {schema}.{table_name}: {r.status_code} {r.text[:200]}")
    return None

def refresh_dataset(ds_id):
    r = session.put(f"{BASE_URL}/api/v1/dataset/{ds_id}/refresh", json={})
    if r.status_code in (200, 201):
        print(f"    Refreshed dataset {ds_id}")
    else:
        print(f"    Refresh failed {ds_id}: {r.status_code}")

def ensure_datasets():
    print("\n=== DATASETS ===")
    ds = {}
    tables = [
        ("gold", "dim_mahasiswa"),
        ("gold", "fact_khs"),
        ("gold", "model_predictions"),
        ("gold", "prediction_by_angkatan_final"),
        ("gold", "model_metrics_final"),
        ("gold", "confusion_matrix_final"),
        ("gold", "classification_report_final"),
    ]
    for schema, table in tables:
        ds[table] = register_dataset(schema, table)
    # Refresh all
    for table, ds_id in ds.items():
        if ds_id:
            refresh_dataset(ds_id)
    return ds

# ============================================================
# CHART HELPERS
# ============================================================
chart_id_counter = [100]

def create_chart(dataset_id, viz_type, params, slice_name):
    payload = {
        "slice_name": slice_name,
        "viz_type": viz_type,
        "datasource_id": dataset_id,
        "datasource_type": "table",
        "params": json.dumps(params),
    }
    r = session.post(f"{BASE_URL}/api/v1/chart/", json=payload)
    if r.status_code in (200, 201):
        cid = r.json().get("id")
        print(f"  Chart: {slice_name} (id={cid})")
        return cid
    else:
        print(f"  Error chart '{slice_name}': {r.status_code} {r.text[:200]}")
        return None

# ============================================================
# SECTION A: KPI UTAMA
# ============================================================
def create_kpi_charts(ds):
    print("\n=== SECTION A: KPI UTAMA ===")
    charts = []

    # KPI 1: Total Mahasiswa (dim_mahasiswa)
    cid = create_chart(ds["dim_mahasiswa"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total Mahasiswa"},
        "header_font_size": 0.4, "subheader_font_size": 0.15,
        "y_axis_format": "SMART_NUMBER",
    }, "Total Mahasiswa")
    if cid: charts.append(cid)

    # KPI 2: Total Training (model_predictions = inference only, so use dim_mahasiswa for training count)
    # Training = dim_mahasiswa with label IS NOT NULL
    cid = create_chart(ds["dim_mahasiswa"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Training"},
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "label", "operator": "is not null", "clause": "WHERE"}],
        "header_font_size": 0.4, "subheader_font_size": 0.15,
        "y_axis_format": "SMART_NUMBER",
    }, "Total Training")
    if cid: charts.append(cid)

    # KPI 3: Total Inference (model_predictions)
    cid = create_chart(ds["model_predictions"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Inference"},
        "header_font_size": 0.4, "subheader_font_size": 0.15,
        "y_axis_format": "SMART_NUMBER",
    }, "Total Inference")
    if cid: charts.append(cid)

    # KPI 4: Tepat Waktu (from model_predictions)
    cid = create_chart(ds["model_predictions"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Tepat Waktu"},
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "prediksi", "operator": "==", "comparator": "Tepat Waktu", "clause": "WHERE"}],
        "header_font_size": 0.4, "subheader_font_size": 0.15,
        "y_axis_format": "SMART_NUMBER",
    }, "Tepat Waktu (Prediksi)")
    if cid: charts.append(cid)

    # KPI 5: Terlambat (from model_predictions)
    cid = create_chart(ds["model_predictions"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Terlambat"},
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "prediksi", "operator": "==", "comparator": "Terlambat", "clause": "WHERE"}],
        "header_font_size": 0.4, "subheader_font_size": 0.15,
        "y_axis_format": "SMART_NUMBER",
    }, "Terlambat (Prediksi)")
    if cid: charts.append(cid)

    # KPI 6: Persentase Tepat Waktu
    cid = create_chart(ds["model_predictions"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(COUNT(CASE WHEN prediksi='Tepat Waktu' THEN 1 END) * 100.0 / NULLIF(COUNT(*),0), 2)", "label": "% TW"},
        "header_font_size": 0.4, "subheader_font_size": 0.15,
        "y_axis_format": ",.2f",
    }, "% Tepat Waktu")
    if cid: charts.append(cid)

    # KPI 7: Persentase Terlambat
    cid = create_chart(ds["model_predictions"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(COUNT(CASE WHEN prediksi='Terlambat' THEN 1 END) * 100.0 / NULLIF(COUNT(*),0), 2)", "label": "% TL"},
        "header_font_size": 0.4, "subheader_font_size": 0.15,
        "y_axis_format": ",.2f",
    }, "% Terlambat")
    if cid: charts.append(cid)

    return charts

# ============================================================
# SECTION B: DISTRIBUSI ANGKATAN
# ============================================================
def create_angkatan_charts(ds):
    print("\n=== SECTION B: DISTRIBUSI ANGKATAN ===")
    charts = []

    cid = create_chart(ds["model_predictions"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah Mahasiswa"}],
        "groupby": [],
        "row_limit": 50,
        "show_legend": False,
        "rich_tooltip": True,
        "x_axis_title": "Angkatan",
        "y_axis_title": "Jumlah Mahasiswa",
        "y_axis_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
    }, "Distribusi Mahasiswa per Angkatan")
    if cid: charts.append(cid)

    return charts

# ============================================================
# SECTION C: PREDIKSI PER ANGKATAN
# ============================================================
def create_prediksi_angkatan_charts(ds):
    print("\n=== SECTION C: PREDIKSI PER ANGKATAN ===")
    charts = []

    # Stacked bar: prediksi per angkatan
    cid = create_chart(ds["model_predictions"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "groupby": ["prediksi"],
        "row_limit": 50,
        "show_legend": True,
        "rich_tooltip": True,
        "stack": True,
        "x_axis_title": "Angkatan",
        "y_axis_title": "Jumlah Mahasiswa",
        "y_axis_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
    }, "Distribusi Prediksi Kelulusan per Angkatan (Stacked)")
    if cid: charts.append(cid)

    # Grouped bar (non-stacked)
    cid = create_chart(ds["model_predictions"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "groupby": ["prediksi"],
        "row_limit": 50,
        "show_legend": True,
        "rich_tooltip": True,
        "stack": False,
        "x_axis_title": "Angkatan",
        "y_axis_title": "Jumlah Mahasiswa",
        "y_axis_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
    }, "Distribusi Prediksi Kelulusan per Angkatan (Grouped)")
    if cid: charts.append(cid)

    # Table: detail per angkatan
    cid = create_chart(ds["prediction_by_angkatan_final"], "table", {
        "all_columns": ["angkatan", "prediksi_tepat_waktu", "prediksi_terlambat", "total"],
        "order_desc": True,
        "row_limit": 10,
        "page_length": 10,
        "include_search": False,
        "show_cell_bars": True,
        "color_pn": True,
    }, "Tabel Prediksi per Angkatan")
    if cid: charts.append(cid)

    return charts

# ============================================================
# SECTION D: DISTRIBUSI PREDIKSI
# ============================================================
def create_distribusi_prediksi_charts(ds):
    print("\n=== SECTION D: DISTRIBUSI PREDIKSI ===")
    charts = []

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
    }, "Distribusi Hasil Prediksi")
    if cid: charts.append(cid)

    return charts

# ============================================================
# SECTION E: DISTRIBUSI LABEL TRAINING
# ============================================================
def create_training_label_charts(ds):
    print("\n=== SECTION E: DISTRIBUSI LABEL TRAINING ===")
    charts = []

    cid = create_chart(ds["dim_mahasiswa"], "pie", {
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "groupby": ["status_kelulusan"],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "label", "operator": "is not null", "clause": "WHERE"}],
        "row_limit": 10,
        "show_labels": True,
        "label_type": "key_value_percent",
        "number_format": "SMART_NUMBER",
        "color_scheme": "supersetColors",
        "donut": True,
        "innerRadius": 50,
        "outerRadius": 80,
    }, "Distribusi Label Data Training")
    if cid: charts.append(cid)

    return charts

# ============================================================
# SECTION F: KONDISI AKADEMIK
# ============================================================
def create_akademik_charts(ds):
    print("\n=== SECTION F: KONDISI AKADEMIK ===")
    charts = []

    # Rata-rata IPK per angkatan
    cid = create_chart(ds["dim_mahasiswa"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ipk), 2)", "label": "Rata-rata IPK"}],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "Lulus", "clause": "WHERE"}],
        "row_limit": 50, "show_legend": False, "rich_tooltip": True,
        "x_axis_title": "Angkatan", "y_axis_title": "IPK",
        "y_axis_format": ",.2f", "color_scheme": "supersetColors",
    }, "Rata-rata IPK per Angkatan (Lulus)")
    if cid: charts.append(cid)

    # Rata-rata Total SKS per angkatan
    cid = create_chart(ds["dim_mahasiswa"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(total_sks), 1)", "label": "Rata-rata Total SKS"}],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "Lulus", "clause": "WHERE"}],
        "row_limit": 50, "show_legend": False, "rich_tooltip": True,
        "x_axis_title": "Angkatan", "y_axis_title": "Total SKS",
        "y_axis_format": "SMART_NUMBER", "color_scheme": "supersetColors",
    }, "Rata-rata Total SKS per Angkatan (Lulus)")
    if cid: charts.append(cid)

    # Rata-rata Selisih SKS per angkatan
    cid = create_chart(ds["dim_mahasiswa"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(selisih_sks), 1)", "label": "Rata-rata Selisih SKS"}],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "Lulus", "clause": "WHERE"}],
        "row_limit": 50, "show_legend": False, "rich_tooltip": True,
        "x_axis_title": "Angkatan", "y_axis_title": "Selisih SKS",
        "y_axis_format": "SMART_NUMBER", "color_scheme": "supersetColors",
    }, "Rata-rata Selisih SKS per Angkatan (Lulus)")
    if cid: charts.append(cid)

    # Rata-rata Lama Studi per angkatan
    cid = create_chart(ds["dim_mahasiswa"], "echarts_bar", {
        "x_axis": "angkatan",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(lama_studi), 2)", "label": "Rata-rata Lama Studi"}],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "Lulus", "clause": "WHERE"}],
        "row_limit": 50, "show_legend": False, "rich_tooltip": True,
        "x_axis_title": "Angkatan", "y_axis_title": "Tahun",
        "y_axis_format": ",.1f", "color_scheme": "supersetColors",
    }, "Rata-rata Lama Studi per Angkatan (Lulus)")
    if cid: charts.append(cid)

    return charts

# ============================================================
# SECTION G: SELISIH SKS
# ============================================================
def create_sks_charts(ds):
    print("\n=== SECTION G: ANALISIS SELISIH SKS ===")
    charts = []

    # Selisih SKS distribution (histogram-like via bar)
    cid = create_chart(ds["dim_mahasiswa"], "echarts_bar", {
        "x_axis": "selisih_sks",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}],
        "row_limit": 50, "show_legend": False, "rich_tooltip": True,
        "x_axis_title": "Selisih SKS", "y_axis_title": "Jumlah Mahasiswa",
        "y_axis_format": "SMART_NUMBER", "color_scheme": "supersetColors",
    }, "Distribusi Selisih SKS (Mahasiswa Aktif)")
    if cid: charts.append(cid)

    # Kategori selisih SKS (use SQL CASE)
    cid = create_chart(ds["dim_mahasiswa"], "pie", {
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "groupby": [{"expressionType": "SQL", "sqlExpression": "CASE WHEN selisih_sks < -10 THEN 'Sangat Tertinggal' WHEN selisih_sks >= -10 AND selisih_sks < 0 THEN 'Di Bawah Target' ELSE 'Memenuhi Target' END", "label": "Kategori SKS"}],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}],
        "row_limit": 10, "show_labels": True,
        "label_type": "key_value_percent", "number_format": "SMART_NUMBER",
        "color_scheme": "supersetColors", "donut": True, "innerRadius": 50, "outerRadius": 80,
    }, "Kategori Selisih SKS (Mahasiswa Aktif)")
    if cid: charts.append(cid)

    return charts

# ============================================================
# SECTION H: MODEL METRICS
# ============================================================
def create_model_charts(ds):
    print("\n=== SECTION H: MODEL METRICS ===")
    charts = []

    # KPI: Accuracy
    cid = create_chart(ds["model_metrics_final"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(test_accuracy * 100, 2)", "label": "Accuracy"},
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "model_name", "operator": "==", "comparator": "GaussianNB_8_features_without_smote", "clause": "WHERE"}],
        "header_font_size": 0.4, "subheader_font_size": 0.15, "y_axis_format": ",.2f",
    }, "Model Accuracy (%)")
    if cid: charts.append(cid)

    # KPI: F1 Score
    cid = create_chart(ds["model_metrics_final"], "big_number_total", {
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(test_f1 * 100, 2)", "label": "F1 Score"},
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "model_name", "operator": "==", "comparator": "GaussianNB_8_features_without_smote", "clause": "WHERE"}],
        "header_font_size": 0.4, "subheader_font_size": 0.15, "y_axis_format": ",.2f",
    }, "Model F1 Score (%)")
    if cid: charts.append(cid)

    # Classification Report table
    cid = create_chart(ds["classification_report_final"], "table", {
        "all_columns": ["class", "precision", "recall", "f1_score", "support"],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "model_name", "operator": "==", "comparator": "GaussianNB_8_features_without_smote", "clause": "WHERE"}],
        "order_desc": True, "row_limit": 10, "page_length": 10,
        "include_search": False, "show_cell_bars": True, "color_pn": True,
    }, "Classification Report (Without SMOTE)")
    if cid: charts.append(cid)

    return charts

# ============================================================
# SECTION I: DETAIL INFERENCE
# ============================================================
def create_detail_charts(ds):
    print("\n=== SECTION I: DETAIL INFERENCE ===")
    charts = []

    # Detail table
    cid = create_chart(ds["model_predictions"], "table", {
        "all_columns": ["id_mahasiswa", "angkatan", "prediksi", "probability"],
        "order_desc": True, "row_limit": 100, "page_length": 50,
        "include_search": True, "show_cell_bars": True, "color_pn": True,
    }, "Detail Mahasiswa Inference")
    if cid: charts.append(cid)

    return charts

# ============================================================
# DASHBOARD
# ============================================================
def create_dashboard(chart_ids, kpi_ids):
    print("\n=== CREATING DASHBOARD ===")

    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
        "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID", "meta": {"text": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa"}},
    }

    row_id = [0]
    chart_idx = [0]

    def add_header(text):
        row_id[0] += 1
        row_key = f"ROW-header-{row_id[0]}"
        position[row_key] = {
            "type": "ROW", "id": row_key, "children": [],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"text": text, "background": "BACKGROUND_TRANSPARENT"},
        }
        position["GRID_ID"]["children"].append(row_key)
        return row_key

    def add_row():
        row_id[0] += 1
        row_key = f"ROW-{row_id[0]}"
        position[row_key] = {
            "type": "ROW", "id": row_key, "children": [],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        position["GRID_ID"]["children"].append(row_key)
        return row_key

    def add_chart(chart_id, parent_row, width=6, height=50):
        chart_idx[0] += 1
        chart_key = f"CHART-{chart_idx[0]}"
        position[chart_key] = {
            "type": "CHART", "id": chart_key, "children": [],
            "parents": ["ROOT_ID", "GRID_ID", parent_row],
            "meta": {"width": width, "height": height, "chartId": chart_id, "sliceName": f"Chart {chart_idx[0]}"},
        }
        position[parent_row]["children"].append(chart_key)
        return chart_key

    # HEADER
    add_header("Dashboard Prediksi Tingkat Kelulusan Mahasiswa")

    # A. KPI
    add_header("A. KPI Utama")
    r = add_row()
    for kid in kpi_ids[:4]:
        add_chart(kid, r, width=3, height=20)
    r2 = add_row()
    for kid in kpi_ids[4:7]:
        add_chart(kid, r2, width=4, height=20)

    # B. Distribusi Angkatan
    add_header("B. Distribusi Mahasiswa per Angkatan")
    r = add_row()
    add_chart(chart_ids["angkatan"][0], r, width=12, height=50)

    # C. Prediksi per Angkatan
    add_header("C. Distribusi Prediksi Kelulusan per Angkatan")
    r = add_row()
    add_chart(chart_ids["prediksi_angkatan"][0], r, width=6, height=50)
    add_chart(chart_ids["prediksi_angkatan"][1], r, width=6, height=50)
    r2 = add_row()
    add_chart(chart_ids["prediksi_angkatan"][2], r2, width=12, height=40)

    # D. Distribusi Prediksi
    add_header("D. Distribusi Hasil Prediksi")
    r = add_row()
    add_chart(chart_ids["distribusi_prediksi"][0], r, width=6, height=50)

    # E. Distribusi Label Training
    add_header("E. Distribusi Label Data Training")
    r = add_row()
    add_chart(chart_ids["training_label"][0], r, width=6, height=50)

    # F. Kondisi Akademik
    add_header("F. Kondisi Akademik")
    r = add_row()
    add_chart(chart_ids["akademik"][0], r, width=6, height=50)
    add_chart(chart_ids["akademik"][1], r, width=6, height=50)
    r2 = add_row()
    add_chart(chart_ids["akademik"][2], r2, width=6, height=50)
    add_chart(chart_ids["akademik"][3], r2, width=6, height=50)

    # G. Selisih SKS
    add_header("G. Analisis Selisih SKS")
    r = add_row()
    add_chart(chart_ids["sks"][0], r, width=6, height=50)
    add_chart(chart_ids["sks"][1], r, width=6, height=50)

    # H. Model Metrics
    add_header("H. Model Metrics")
    r = add_row()
    add_chart(chart_ids["model"][0], r, width=4, height=20)
    add_chart(chart_ids["model"][1], r, width=4, height=20)
    r2 = add_row()
    add_chart(chart_ids["model"][2], r2, width=12, height=50)

    # I. Detail Inference
    add_header("I. Detail Mahasiswa Inference")
    r = add_row()
    add_chart(chart_ids["detail"][0], r, width=12, height=80)

    # Create/update dashboard
    # Check existing dashboard
    r = session.get(f"{BASE_URL}/api/v1/dashboard/?q=(page_size:200)")
    dashboards = r.json().get("result", [])
    existing_dash = None
    for d in dashboards:
        if d.get("dashboard_title") == "Dashboard Prediksi Tingkat Kelulusan Mahasiswa":
            existing_dash = d["id"]
            break

    payload = {
        "dashboard_title": "Dashboard Prediksi Tingkat Kelulusan Mahasiswa",
        "slug": "dashboard-prediksi-kelulusan",
        "published": True,
        "position_json": json.dumps(position),
    }

    if existing_dash:
        r = session.put(f"{BASE_URL}/api/v1/dashboard/{existing_dash}", json=payload)
        dash_id = existing_dash
        print(f"  Updated dashboard: id={dash_id}")
    else:
        r = session.post(f"{BASE_URL}/api/v1/dashboard/", json=payload)
        dash_id = r.json().get("id") if r.status_code in (200, 201) else None
        print(f"  Created dashboard: id={dash_id}")

    return dash_id

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("SUPERSET DASHBOARD SETUP - FINAL")
    print("=" * 70)

    login()
    ds = ensure_datasets()

    # Create all charts
    kpi_charts = create_kpi_charts(ds)
    angkatan_charts = create_angkatan_charts(ds)
    prediksi_angkatan_charts = create_prediksi_angkatan_charts(ds)
    distribusi_prediksi_charts = create_distribusi_prediksi_charts(ds)
    training_label_charts = create_training_label_charts(ds)
    akademik_charts = create_akademik_charts(ds)
    sks_charts = create_sks_charts(ds)
    model_charts = create_model_charts(ds)
    detail_charts = create_detail_charts(ds)

    chart_ids = {
        "angkatan": angkatan_charts,
        "prediksi_angkatan": prediksi_angkatan_charts,
        "distribusi_prediksi": distribusi_prediksi_charts,
        "training_label": training_label_charts,
        "akademik": akademik_charts,
        "sks": sks_charts,
        "model": model_charts,
        "detail": detail_charts,
    }

    dash_id = create_dashboard(chart_ids, kpi_charts)

    print()
    print("=" * 70)
    print("SETUP COMPLETE")
    print("=" * 70)
    if dash_id:
        print(f"Dashboard URL: http://localhost:8088/superset/dashboard/{dash_id}/")
    total = (len(kpi_charts) + len(angkatan_charts) + len(prediksi_angkatan_charts) +
             len(distribusi_prediksi_charts) + len(training_label_charts) + len(akademik_charts) +
             len(sks_charts) + len(model_charts) + len(detail_charts))
    print(f"Total charts: {total}")

if __name__ == "__main__":
    main()
