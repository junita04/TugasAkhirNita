"""
Phase 7: Register new v2 datasets in Superset and create prediction dashboard charts.
Uses Flask app context to avoid CSRF issues.
"""
import sys
sys.path.insert(0, '/app')

from superset.app import create_app
from superset import db
import json

app = create_app()
app.app_context().push()

from superset.connectors.sqla.models import SqlaTable, Database
from superset.models.slice import Slice
from superset.models.dashboard import Dashboard

# =====================================================
# Find Trino database
# =====================================================
trino_db = db.session.query(Database).filter_by(database_name="Academic Trino").first()
if not trino_db:
    print("ERROR: Academic Trino database not found!")
    sys.exit(1)
print(f"Database: {trino_db.database_name} (ID={trino_db.id})")

# =====================================================
# Register new datasets
# =====================================================
new_datasets = [
    ("model_predictions_v2", "gold"),
    ("prediction_by_angkatan_v2", "gold"),
    ("training_dataset_v2", "feature_store"),
    ("inference_dataset_v2", "feature_store"),
]

created_datasets = {}
for table_name, schema in new_datasets:
    # Check if already exists
    existing = db.session.query(SqlaTable).filter_by(
        table_name=table_name, schema=schema, database_id=trino_db.id
    ).first()
    
    if existing:
        print(f"  Dataset already exists: {table_name} (ID={existing.id})")
        # Refresh columns
        existing.sync()
        db.session.commit()
        created_datasets[table_name] = existing.id
        print(f"    Columns refreshed: {len(existing.columns)} cols")
    else:
        ds = SqlaTable(
            table_name=table_name,
            schema=schema,
            database_id=trino_db.id,
        )
        ds.sync()
        db.session.add(ds)
        db.session.commit()
        created_datasets[table_name] = ds.id
        print(f"  Created dataset: {table_name} (ID={ds.id}, {len(ds.columns)} cols)")

print(f"\nDataset IDs: {created_datasets}")

# =====================================================
# Get dataset IDs for chart creation
# =====================================================
pred_v2_id = created_datasets["model_predictions_v2"]
agg_v2_id = created_datasets["prediction_by_angkatan_v2"]
train_v2_id = created_datasets["training_dataset_v2"]

print(f"\nUsing datasets:")
print(f"  model_predictions_v2: ID={pred_v2_id}")
print(f"  prediction_by_angkatan_v2: ID={agg_v2_id}")
print(f"  training_dataset_v2: ID={train_v2_id}")

# =====================================================
# Create charts for Dashboard 3 (Prediction Dashboard)
# =====================================================
print("\n" + "=" * 70)
print("CREATING PREDICTION DASHBOARD CHARTS")
print("=" * 70)

charts_to_create = []

# 1. KPI: Total Mahasiswa
charts_to_create.append({
    "name": "Total Mahasiswa (V2)",
    "viz_type": "big_number_total",
    "datasource_id": pred_v2_id,
    "datasource_type": "table",
    "params": json.dumps({
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total Mahasiswa"},
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
    }),
    "query_context": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": [], "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total Mahasiswa"}], "row_limit": 10000}],
        "result_format": "json",
        "result_type": "full",
    }),
})

# 2. KPI: Tepat Waktu
charts_to_create.append({
    "name": "Tepat Waktu (V2)",
    "viz_type": "big_number_total",
    "datasource_id": pred_v2_id,
    "datasource_type": "table",
    "params": json.dumps({
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Tepat Waktu"},
        "adhoc_filters": [{"clause": "WHERE", "expressionType": "SIMPLE", "subject": "Prediksi", "operator": "==", "comparator": "0", "filterOptionName": "f1"}],
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
    }),
    "query_context": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": [], "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Tepat Waktu"}], "filters": [{"col": "Prediksi", "op": "==", "val": "0"}], "row_limit": 10000}],
        "result_format": "json",
        "result_type": "full",
    }),
})

# 3. KPI: Terlambat
charts_to_create.append({
    "name": "Terlambat (V2)",
    "viz_type": "big_number_total",
    "datasource_id": pred_v2_id,
    "datasource_type": "table",
    "params": json.dumps({
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Terlambat"},
        "adhoc_filters": [{"clause": "WHERE", "expressionType": "SIMPLE", "subject": "Prediksi", "operator": "==", "comparator": "1", "filterOptionName": "f1"}],
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
    }),
    "query_context": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": [], "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Terlambat"}], "filters": [{"col": "Prediksi", "op": "==", "val": "1"}], "row_limit": 10000}],
        "result_format": "json",
        "result_type": "full",
    }),
})

# 4. KPI: % Tepat Waktu
charts_to_create.append({
    "name": "% Tepat Waktu (V2)",
    "viz_type": "big_number_total",
    "datasource_id": pred_v2_id,
    "datasource_type": "table",
    "params": json.dumps({
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(SUM(CASE WHEN Prediksi=0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)", "label": "% Tepat Waktu"},
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
    }),
    "query_context": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": [], "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(SUM(CASE WHEN Prediksi=0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)", "label": "% Tepat Waktu"}], "row_limit": 10000}],
        "result_format": "json",
        "result_type": "full",
    }),
})

# 5. KPI: % Terlambat
charts_to_create.append({
    "name": "% Terlambat (V2)",
    "viz_type": "big_number_total",
    "datasource_id": pred_v2_id,
    "datasource_type": "table",
    "params": json.dumps({
        "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(SUM(CASE WHEN Prediksi=1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)", "label": "% Terlambat"},
        "header_font_size": 0.4,
        "subheader_font_size": 0.15,
    }),
    "query_context": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": [], "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(SUM(CASE WHEN Prediksi=1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)", "label": "% Terlambat"}], "row_limit": 10000}],
        "result_format": "json",
        "result_type": "full",
    }),
})

# 6. Pie: Distribusi Prediksi
charts_to_create.append({
    "name": "Distribusi Prediksi (V2)",
    "viz_type": "pie",
    "datasource_id": pred_v2_id,
    "datasource_type": "table",
    "params": json.dumps({
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"},
        "groupby": ["Prediksi_Label"],
        "show_labels": True,
        "label_type": "key_value_percent",
    }),
    "query_context": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": ["Prediksi_Label"], "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"}], "row_limit": 10000}],
        "result_format": "json",
        "result_type": "full",
    }),
})

# 7. Bar: Prediksi per Angkatan (Stacked)
charts_to_create.append({
    "name": "Prediksi per Angkatan (V2)",
    "viz_type": "echarts_timeseries_bar",
    "datasource_id": agg_v2_id,
    "datasource_type": "table",
    "params": json.dumps({
        "x_axis": "angkatan",
        "metrics": [
            {"expressionType": "SQL", "sqlExpression": "prediksi_tepat_waktu", "label": "Tepat Waktu"},
            {"expressionType": "SQL", "sqlExpression": "prediksi_terlambat", "label": "Terlambat"},
        ],
        "groupby": [],
        "stack": True,
        "show_value": True,
    }),
    "query_context": json.dumps({
        "datasource": {"id": agg_v2_id, "type": "table"},
        "queries": [{"columns": ["angkatan"], "metrics": [{"expressionType": "SQL", "sqlExpression": "prediksi_tepat_waktu", "label": "Tepat Waktu"}, {"expressionType": "SQL", "sqlExpression": "prediksi_terlambat", "label": "Terlambat"}], "row_limit": 10000}],
        "result_format": "json",
        "result_type": "full",
    }),
})

# 8. Bar: Persentase per Angkatan
charts_to_create.append({
    "name": "Persentase Prediksi per Angkatan (V2)",
    "viz_type": "echarts_timeseries_bar",
    "datasource_id": agg_v2_id,
    "datasource_type": "table",
    "params": json.dumps({
        "x_axis": "angkatan",
        "metrics": [
            {"expressionType": "SQL", "sqlExpression": "persentase_tepat_waktu", "label": "% Tepat Waktu"},
            {"expressionType": "SQL", "sqlExpression": "persentase_terlambat", "label": "% Terlambat"},
        ],
        "groupby": [],
        "stack": False,
        "show_value": True,
    }),
    "query_context": json.dumps({
        "datasource": {"id": agg_v2_id, "type": "table"},
        "queries": [{"columns": ["angkatan"], "metrics": [{"expressionType": "SQL", "sqlExpression": "persentase_tepat_waktu", "label": "% Tepat Waktu"}, {"expressionType": "SQL", "sqlExpression": "persentase_terlambat", "label": "% Terlambat"}], "row_limit": 10000}],
        "result_format": "json",
        "result_type": "full",
    }),
})

# 9. Histogram: Distribusi Probabilitas Tepat Waktu
charts_to_create.append({
    "name": "Distribusi Prob Tepat Waktu (V2)",
    "viz_type": "echarts_area",
    "datasource_id": pred_v2_id,
    "datasource_type": "table",
    "params": json.dumps({
        "x_axis": "Probabilitas_Tepat_Waktu",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"}],
        "groupby": [],
        "row_limit": 10000,
        "extra_form_data": {"time_grain_sqla": "P1D"},
    }),
    "query_context": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": ["Probabilitas_Tepat_Waktu"], "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"}], "row_limit": 10000}],
        "result_format": "json",
        "result_type": "full",
    }),
})

# 10. Table: Detail Mahasiswa
charts_to_create.append({
    "name": "Detail Prediksi Mahasiswa (V2)",
    "viz_type": "table",
    "datasource_id": pred_v2_id,
    "datasource_type": "table",
    "params": json.dumps({
        "all_columns": ["id_mahasiswa", "angkatan", "ip", "ipk", "total_sks", "jumlah_mk", "selisih_sks", "Probabilitas_Tepat_Waktu", "Probabilitas_Terlambat", "Prediksi_Label"],
        "order_by_cols": [],
        "row_limit": 100,
        "page_length": 0,
        "include_search": True,
    }),
    "query_context": json.dumps({
        "datasource": {"id": pred_v2_id, "type": "table"},
        "queries": [{"columns": ["id_mahasiswa", "angkatan", "ip", "ipk", "total_sks", "jumlah_mk", "selisih_sks", "Probabilitas_Tepat_Waktu", "Probabilitas_Terlambat", "Prediksi_Label"], "row_limit": 100}],
        "result_format": "json",
        "result_type": "full",
    }),
})

# 11. Pie: Distribusi Label Training V2
charts_to_create.append({
    "name": "Distribusi Label Training (V2)",
    "viz_type": "pie",
    "datasource_id": train_v2_id,
    "datasource_type": "table",
    "params": json.dumps({
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"},
        "groupby": ["label"],
        "show_labels": True,
        "label_type": "key_value_percent",
    }),
    "query_context": json.dumps({
        "datasource": {"id": train_v2_id, "type": "table"},
        "queries": [{"columns": ["label"], "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"}], "row_limit": 10000}],
        "result_format": "json",
        "result_type": "full",
    }),
})

# =====================================================
# Create all charts
# =====================================================
created_chart_ids = []
for i, chart_def in enumerate(charts_to_create):
    # Check if chart with same name exists
    existing = db.session.query(Slice).filter_by(slice_name=chart_def["name"]).first()
    if existing:
        print(f"  Chart already exists: {chart_def['name']} (ID={existing.id})")
        created_chart_ids.append(existing.id)
        continue
    
    s = Slice(
        slice_name=chart_def["name"],
        viz_type=chart_def["viz_type"],
        datasource_id=chart_def["datasource_id"],
        datasource_type=chart_def["datasource_type"],
        params=chart_def["params"],
        query_context=chart_def["query_context"],
    )
    db.session.add(s)
    db.session.commit()
    created_chart_ids.append(s.id)
    print(f"  Created chart: {chart_def['name']} (ID={s.id})")

print(f"\nChart IDs: {created_chart_ids}")

# =====================================================
# Update Dashboard 3 layout
# =====================================================
print("\n" + "=" * 70)
print("UPDATING DASHBOARD 3 LAYOUT")
print("=" * 70)

dash = db.session.query(Dashboard).get(3)
if not dash:
    print("ERROR: Dashboard 3 not found!")
    sys.exit(1)

print(f"Dashboard: {dash.dashboard_title}")

# Build new position_json with v2 charts
pos = {
    "DASHBOARD_VERSION_KEY": "v2",
    "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
    "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": ["ROW-kpi", "ROW-charts", "ROW-table"], "parents": []},
    "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID", "meta": {"text": dash.dashboard_title}},
}

# Row 1: KPIs
pos["ROW-kpi"] = {
    "type": "ROW", "id": "ROW-kpi",
    "children": ["CHART-tw", "CHART-tpw", "CHART-tl", "CHART-ptw", "CHART-ptl"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

kpi_charts = [
    ("CHART-tw", created_chart_ids[0], "Total Mahasiswa (V2)"),
    ("CHART-tpw", created_chart_ids[1], "Tepat Waktu (V2)"),
    ("CHART-tl", created_chart_ids[2], "Terlambat (V2)"),
    ("CHART-ptw", created_chart_ids[3], "% Tepat Waktu (V2)"),
    ("CHART-ptl", created_chart_ids[4], "% Terlambat (V2)"),
]
for chart_id, chart_key, chart_name in kpi_charts:
    pos[chart_id] = {
        "type": "CHART", "id": chart_id,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-kpi"],
        "meta": {"width": 4, "height": 8, "chartId": chart_key, "sliceName": chart_name}
    }

# Row 2: Charts
pos["ROW-charts"] = {
    "type": "ROW", "id": "ROW-charts",
    "children": ["CHART-pie", "CHART-bar1", "CHART-bar2", "CHART-hist"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

chart_defs = [
    ("CHART-pie", created_chart_ids[5], "Distribusi Prediksi (V2)"),
    ("CHART-bar1", created_chart_ids[6], "Prediksi per Angkatan (V2)"),
    ("CHART-bar2", created_chart_ids[7], "Persentase Prediksi per Angkatan (V2)"),
    ("CHART-hist", created_chart_ids[8], "Distribusi Prob Tepat Waktu (V2)"),
]
for chart_id, chart_key, chart_name in chart_defs:
    pos[chart_id] = {
        "type": "CHART", "id": chart_id,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", "ROW-charts"],
        "meta": {"width": 6, "height": 10, "chartId": chart_key, "sliceName": chart_name}
    }

# Row 3: Table
pos["ROW-table"] = {
    "type": "ROW", "id": "ROW-table",
    "children": ["CHART-table", "CHART-train-pie"],
    "parents": ["ROOT_ID", "GRID_ID"],
    "meta": {"background": "BACKGROUND_TRANSPARENT"}
}

pos["CHART-table"] = {
    "type": "CHART", "id": "CHART-table",
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-table"],
    "meta": {"width": 12, "height": 12, "chartId": created_chart_ids[9], "sliceName": "Detail Prediksi Mahasiswa (V2)"}
}

pos["CHART-train-pie"] = {
    "type": "CHART", "id": "CHART-train-pie",
    "children": [],
    "parents": ["ROOT_ID", "GRID_ID", "ROW-table"],
    "meta": {"width": 6, "height": 8, "chartId": created_chart_ids[10], "sliceName": "Distribusi Label Training (V2)"}
}

dash.position_json = json.dumps(pos)

# Add new charts to dashboard
existing_slice_ids = [s.id for s in dash.slices]
for cid in created_chart_ids:
    if cid not in existing_slice_ids:
        s = db.session.query(Slice).get(cid)
        if s:
            dash.slices.append(s)

db.session.commit()
print(f"Dashboard updated with {len(created_chart_ids)} charts")
print(f"URL: http://localhost:8088/superset/dashboard/3/")

print("\n" + "=" * 70)
print("PHASE 7 COMPLETE")
print("=" * 70)
