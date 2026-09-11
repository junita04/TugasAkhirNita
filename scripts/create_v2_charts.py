"""
Create prediction dashboard charts using the registered v2 datasets.
"""
import sys
sys.path.insert(0, '/app')

from superset.app import create_app
from superset import db
import json

app = create_app()
app.app_context().push()

from superset.models.slice import Slice
from superset.models.dashboard import Dashboard

# Dataset IDs
pred_v2_id = 36  # model_predictions_v2
agg_v2_id = 37   # prediction_by_angkatan_v2
train_v2_id = 38  # training_dataset_v2

print("=" * 70)
print("CREATING PREDICTION DASHBOARD CHARTS (V2)")
print("=" * 70)

charts = []

# 1. KPI: Total Mahasiswa
charts.append({
    "name": "Total Mahasiswa (V2)",
    "viz_type": "big_number_total",
    "did": pred_v2_id,
    "params": json.dumps({
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total Mahasiswa"},
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
    }),
    "qc": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": [], "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total Mahasiswa"}], "row_limit": 10000}],
        "result_format": "json", "result_type": "full",
    }),
})

# 2. KPI: Tepat Waktu
charts.append({
    "name": "Tepat Waktu (V2)",
    "viz_type": "big_number_total",
    "did": pred_v2_id,
    "params": json.dumps({
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Tepat Waktu"},
        "header_font_size": 0.4, "subheader_font_size": 0.15,
    }),
    "qc": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": [], "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Tepat Waktu"}], "filters": [{"col": "Prediksi", "op": "==", "val": 0}], "row_limit": 10000}],
        "result_format": "json", "result_type": "full",
    }),
})

# 3. KPI: Terlambat
charts.append({
    "name": "Terlambat (V2)",
    "viz_type": "big_number_total",
    "did": pred_v2_id,
    "params": json.dumps({
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Terlambat"},
        "header_font_size": 0.4, "subheader_font_size": 0.15,
    }),
    "qc": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": [], "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Terlambat"}], "filters": [{"col": "Prediksi", "op": "==", "val": 1}], "row_limit": 10000}],
        "result_format": "json", "result_type": "full",
    }),
})

# 4. KPI: % Tepat Waktu
charts.append({
    "name": "% Tepat Waktu (V2)",
    "viz_type": "big_number_total",
    "did": pred_v2_id,
    "params": json.dumps({
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(SUM(CASE WHEN Prediksi=0 THEN 1 ELSE 0 END)*100.0/COUNT(*),2)", "label": "% Tepat Waktu"},
        "header_font_size": 0.4, "subheader_font_size": 0.15,
    }),
    "qc": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": [], "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(SUM(CASE WHEN Prediksi=0 THEN 1 ELSE 0 END)*100.0/COUNT(*),2)", "label": "% Tepat Waktu"}], "row_limit": 10000}],
        "result_format": "json", "result_type": "full",
    }),
})

# 5. KPI: % Terlambat
charts.append({
    "name": "% Terlambat (V2)",
    "viz_type": "big_number_total",
    "did": pred_v2_id,
    "params": json.dumps({
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(SUM(CASE WHEN Prediksi=1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2)", "label": "% Terlambat"},
        "header_font_size": 0.4, "subheader_font_size": 0.15,
    }),
    "qc": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": [], "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(SUM(CASE WHEN Prediksi=1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2)", "label": "% Terlambat"}], "row_limit": 10000}],
        "result_format": "json", "result_type": "full",
    }),
})

# 6. Pie: Distribusi Prediksi
charts.append({
    "name": "Distribusi Prediksi (V2)",
    "viz_type": "pie",
    "did": pred_v2_id,
    "params": json.dumps({
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"},
        "groupby": ["Prediksi_Label"],
        "show_labels": True,
        "label_type": "key_value_percent",
    }),
    "qc": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": ["Prediksi_Label"], "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"}], "row_limit": 10000}],
        "result_format": "json", "result_type": "full",
    }),
})

# 7. Bar: Prediksi per Angkatan
charts.append({
    "name": "Prediksi per Angkatan (V2)",
    "viz_type": "echarts_timeseries_bar",
    "did": agg_v2_id,
    "params": json.dumps({
        "x_axis": "angkatan",
        "metrics": [
            {"expressionType": "SQL", "sqlExpression": "prediksi_tepat_waktu", "label": "Tepat Waktu"},
            {"expressionType": "SQL", "sqlExpression": "prediksi_terlambat", "label": "Terlambat"},
        ],
        "groupby": [], "stack": True, "show_value": True,
    }),
    "qc": json.dumps({
        "datasource": {"id": agg_v2_id, "type": "table"},
        "queries": [{"columns": ["angkatan"], "metrics": [{"expressionType": "SQL", "sqlExpression": "prediksi_tepat_waktu", "label": "Tepat Waktu"}, {"expressionType": "SQL", "sqlExpression": "prediksi_terlambat", "label": "Terlambat"}], "row_limit": 10000}],
        "result_format": "json", "result_type": "full",
    }),
})

# 8. Bar: Persentase per Angkatan
charts.append({
    "name": "Persentase Prediksi per Angkatan (V2)",
    "viz_type": "echarts_timeseries_bar",
    "did": agg_v2_id,
    "params": json.dumps({
        "x_axis": "angkatan",
        "metrics": [
            {"expressionType": "SQL", "sqlExpression": "persentase_tepat_waktu", "label": "% Tepat Waktu"},
            {"expressionType": "SQL", "sqlExpression": "persentase_terlambat", "label": "% Terlambat"},
        ],
        "groupby": [], "stack": False, "show_value": True,
    }),
    "qc": json.dumps({
        "datasource": {"id": agg_v2_id, "type": "table"},
        "queries": [{"columns": ["angkatan"], "metrics": [{"expressionType": "SQL", "sqlExpression": "persentase_tepat_waktu", "label": "% Tepat Waktu"}, {"expressionType": "SQL", "sqlExpression": "persentase_terlambat", "label": "% Terlambat"}], "row_limit": 10000}],
        "result_format": "json", "result_type": "full",
    }),
})

# 9. Table: Detail Mahasiswa
charts.append({
    "name": "Detail Prediksi Mahasiswa (V2)",
    "viz_type": "table",
    "did": pred_v2_id,
    "params": json.dumps({
        "all_columns": ["id_mahasiswa", "angkatan", "ip", "ipk", "total_sks", "jumlah_mk", "selisih_sks", "Probabilitas_Tepat_Waktu", "Probabilitas_Terlambat", "Prediksi_Label"],
        "order_by_cols": [],
        "row_limit": 100,
        "page_length": 0,
        "include_search": True,
    }),
    "qc": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": ["id_mahasiswa", "angkatan", "ip", "ipk", "total_sks", "jumlah_mk", "selisih_sks", "Probabilitas_Tepat_Waktu", "Probabilitas_Terlambat", "Prediksi_Label"], "row_limit": 100}],
        "result_format": "json", "result_type": "full",
    }),
})

# 10. Pie: Distribusi Label Training V2
charts.append({
    "name": "Distribusi Label Training (V2)",
    "viz_type": "pie",
    "did": train_v2_id,
    "params": json.dumps({
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"},
        "groupby": ["label"],
        "show_labels": True,
        "label_type": "key_value_percent",
    }),
    "qc": json.dumps({
        "datasource": {"id": train_v2_id, "type": "table"},
        "queries": [{"columns": ["label"], "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"}], "row_limit": 10000}],
        "result_format": "json", "result_type": "full",
    }),
})

# Create charts
chart_ids = []
for c in charts:
    existing = db.session.query(Slice).filter_by(slice_name=c["name"]).first()
    if existing:
        print(f"  Exists: {c['name']} (ID={existing.id})")
        chart_ids.append(existing.id)
        continue
    
    s = Slice(
        slice_name=c["name"],
        viz_type=c["viz_type"],
        datasource_id=c["did"],
        datasource_type="table",
        params=c["params"],
        query_context=c["qc"],
    )
    db.session.add(s)
    db.session.commit()
    chart_ids.append(s.id)
    print(f"  Created: {c['name']} (ID={s.id})")

print(f"\nChart IDs: {chart_ids}")

# =====================================================
# Update Dashboard 3
# =====================================================
print("\n" + "=" * 70)
print("UPDATING DASHBOARD 3")
print("=" * 70)

dash = db.session.query(Dashboard).get(3)
print(f"Dashboard: {dash.dashboard_title}")

pos = {
    "DASHBOARD_VERSION_KEY": "v2",
    "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
    "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": ["ROW-kpi", "ROW-charts", "ROW-table"], "parents": []},
    "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID", "meta": {"text": dash.dashboard_title}},
}

# Row 1: KPIs
pos["ROW-kpi"] = {
    "type": "ROW", "id": "ROW-kpi",
    "children": ["CHART-0", "CHART-1", "CHART-2", "CHART-3", "CHART-4"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}
kpi_names = ["Total Mahasiswa (V2)", "Tepat Waktu (V2)", "Terlambat (V2)", "% Tepat Waktu (V2)", "% Terlambat (V2)"]
for i, name in enumerate(kpi_names):
    pos[f"CHART-{i}"] = {
        "type": "CHART", "id": f"CHART-{i}",
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-kpi"],
        "meta": {"width": 4, "height": 8, "chartId": chart_ids[i], "sliceName": name}
    }

# Row 2: Charts
pos["ROW-charts"] = {
    "type": "ROW", "id": "ROW-charts",
    "children": ["CHART-5", "CHART-6", "CHART-7"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}
chart_names = ["Distribusi Prediksi (V2)", "Prediksi per Angkatan (V2)", "Persentase Prediksi per Angkatan (V2)"]
for i, name in enumerate(chart_names):
    idx = 5 + i
    pos[f"CHART-{idx}"] = {
        "type": "CHART", "id": f"CHART-{idx}",
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-charts"],
        "meta": {"width": 8, "height": 10, "chartId": chart_ids[idx], "sliceName": name}
    }

# Row 3: Table + Training Pie
pos["ROW-table"] = {
    "type": "ROW", "id": "ROW-table",
    "children": ["CHART-8", "CHART-9"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}
pos["CHART-8"] = {
    "type": "CHART", "id": "CHART-8",
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-table"],
    "meta": {"width": 12, "height": 12, "chartId": chart_ids[8], "sliceName": "Detail Prediksi Mahasiswa (V2)"}
}
pos["CHART-9"] = {
    "type": "CHART", "id": "CHART-9",
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-table"],
    "meta": {"width": 6, "height": 8, "chartId": chart_ids[9], "sliceName": "Distribusi Label Training (V2)"}
}

dash.position_json = json.dumps(pos)

# Add charts to dashboard
existing_slice_ids = [s.id for s in dash.slices]
for cid in chart_ids:
    if cid not in existing_slice_ids:
        s = db.session.query(Slice).get(cid)
        if s:
            dash.slices.append(s)

db.session.commit()
print(f"Dashboard updated with {len(chart_ids)} charts")
print(f"URL: http://localhost:8088/superset/dashboard/3/")

# =====================================================
# Validate charts via API
# =====================================================
print("\n" + "=" * 70)
print("VALIDATING CHARTS VIA API")
print("=" * 70)

import requests
SUPERSET = "http://localhost:8088"
r = requests.post(f"{SUPERSET}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
token = r.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

all_pass = True
for i, cid in enumerate(chart_ids):
    r = requests.get(f"{SUPERSET}/api/v1/chart/{cid}/data/", headers=headers, params={"force": "true"})
    s = db.session.query(Slice).get(cid)
    if r.status_code == 200:
        data = r.json()
        if "result" in data and isinstance(data["result"], list) and len(data["result"]) > 0:
            row_count = len(data["result"][0].get("data", []))
            print(f"  PASS  ID={cid:3d}  {s.viz_type:25s}  {s.slice_name:35s}  rows={row_count}")
        else:
            print(f"  FAIL  ID={cid:3d}  {s.viz_type:25s}  {s.slice_name:35s}  empty result")
            all_pass = False
    else:
        print(f"  FAIL  ID={cid:3d}  {s.viz_type:25s}  {s.slice_name:35s}  HTTP {r.status_code}")
        all_pass = False

print(f"\nALL CHARTS PASS: {all_pass}")
print("=" * 70)
