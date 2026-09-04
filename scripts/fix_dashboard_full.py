"""
Fix Dashboard 4 - Rebuild ALL charts using dataset ID=27 (dim_mahasiswa).
This ensures all charts have access to all columns.
"""
import sys
sys.path.insert(0, '/app')

from superset.app import create_app
from superset import db
import json

app = create_app()
app.app_context().push()

from superset.models.dashboard import Dashboard
from superset.models.slice import Slice
from superset.connectors.sqla.models import SqlaTable

print("=" * 70)
print("REBUILD DASHBOARD 4 - ALL CHARTS ON DATASET 27")
print("=" * 70)

DATASET_ID = 27  # dim_mahasiswa

# ============================================================
# Step 1: Delete old charts in Dashboard 4
# ============================================================
dashboard = db.session.query(Dashboard).get(4)
position = json.loads(dashboard.position_json) if dashboard.position_json else {}
old_chart_ids = [v.get("meta", {}).get("chartId") for k, v in position.items() if k.startswith("CHART-")]

print(f"\nOld chart IDs to remove: {old_chart_ids}")
for cid in old_chart_ids:
    chart = db.session.query(Slice).get(cid)
    if chart:
        db.session.delete(chart)
db.session.commit()
print(f"Deleted {len(old_chart_ids)} old charts")

# ============================================================
# Step 2: Create all new charts on dataset 27
# ============================================================
charts_config = [
    # KPIs (big_number_total)
    {
        "name": "Total Mahasiswa",
        "viz_type": "big_number_total",
        "params": {
            "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(DISTINCT id_mahasiswa)", "label": "Total Mahasiswa"},
            "header_font_size": 0.4,
            "subheader_font_size": 0.15,
            "y_axis_format": ",.0f",
            "header_color": "#000000"
        }
    },
    {
        "name": "Mahasiswa Aktif",
        "viz_type": "big_number_total",
        "params": {
            "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(DISTINCT CASE WHEN status_mahasiswa='AKTIF' THEN id_mahasiswa END)", "label": "Mahasiswa Aktif"},
            "header_font_size": 0.4,
            "subheader_font_size": 0.15,
            "y_axis_format": ",.0f",
            "header_color": "#000000"
        }
    },
    {
        "name": "Mahasiswa Lulus",
        "viz_type": "big_number_total",
        "params": {
            "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(DISTINCT CASE WHEN status_mahasiswa='Lulus' THEN id_mahasiswa END)", "label": "Mahasiswa Lulus"},
            "header_font_size": 0.4,
            "subheader_font_size": 0.15,
            "y_axis_format": ",.0f",
            "header_color": "#000000"
        }
    },
    {
        "name": "Tepat Waktu",
        "viz_type": "big_number_total",
        "params": {
            "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(DISTINCT CASE WHEN label=0 THEN id_mahasiswa END)", "label": "Tepat Waktu"},
            "header_font_size": 0.4,
            "subheader_font_size": 0.15,
            "y_axis_format": ",.0f",
            "header_color": "#1fa855"
        }
    },
    {
        "name": "Terlambat",
        "viz_type": "big_number_total",
        "params": {
            "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(DISTINCT CASE WHEN label=1 THEN id_mahasiswa END)", "label": "Terlambat"},
            "header_font_size": 0.4,
            "subheader_font_size": 0.15,
            "y_axis_format": ",.0f",
            "header_color": "#e04355"
        }
    },
    {
        "name": "Rata-rata IPK",
        "viz_type": "big_number_total",
        "params": {
            "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ipk), 2)", "label": "Rata-rata IPK"},
            "header_font_size": 0.4,
            "subheader_font_size": 0.15,
            "y_axis_format": ",.2f",
            "header_color": "#000000"
        }
    },
    {
        "name": "Rata-rata IP",
        "viz_type": "big_number_total",
        "params": {
            "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ip), 2)", "label": "Rata-rata IP"},
            "header_font_size": 0.4,
            "subheader_font_size": 0.15,
            "y_axis_format": ",.2f",
            "header_color": "#000000"
        }
    },
    {
        "name": "Rata-rata Total SKS",
        "viz_type": "big_number_total",
        "params": {
            "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(AVG(total_sks), 1)", "label": "Rata-rata Total SKS"},
            "header_font_size": 0.4,
            "subheader_font_size": 0.15,
            "y_axis_format": ",.0f",
            "header_color": "#000000"
        }
    },
    # Distribution charts
    {
        "name": "Distribusi Mahasiswa per Angkatan",
        "viz_type": "echarts_timeseries_bar",
        "params": {
            "x_axis": "angkatan",
            "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(DISTINCT id_mahasiswa)", "label": "Jumlah"}],
            "row_limit": 100,
            "truncate_metric": True,
            "show_legend": True,
            "stack": False,
            "orientation": "vertical",
            "color_scheme": "supersetColors",
            "rich_tooltip": True,
            "show_bar_value": True,
        }
    },
    {
        "name": "Distribusi Status Mahasiswa",
        "viz_type": "pie",
        "params": {
            "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(DISTINCT id_mahasiswa)", "label": "Jumlah"},
            "groupby": ["status_mahasiswa"],
            "row_limit": 100,
            "show_labels": True,
            "label_type": "key_percent",
            "number_format": ",.0f",
            "show_legend": True,
            "color_scheme": "supersetColors",
        }
    },
    {
        "name": "Distribusi Status Kelulusan",
        "viz_type": "pie",
        "params": {
            "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(DISTINCT id_mahasiswa)", "label": "Jumlah"},
            "groupby": ["status_kelulusan"],
            "row_limit": 100,
            "show_labels": True,
            "label_type": "key_percent",
            "number_format": ",.0f",
            "show_legend": True,
            "color_scheme": "supersetColors",
            "adhoc_filters": [{"clause": "WHERE", "expressionType": "SIMPLE", "subject": "status_kelulusan", "operator": "IS NOT NULL", "comparator": None, "filterOptionName": "filter_not_null"}],
        }
    },
    {
        "name": "Status Kelulusan per Angkatan",
        "viz_type": "echarts_timeseries_bar",
        "params": {
            "x_axis": "angkatan",
            "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(DISTINCT id_mahasiswa)", "label": "Jumlah"}],
            "groupby": ["status_kelulusan"],
            "row_limit": 100,
            "stack": True,
            "show_legend": True,
            "orientation": "vertical",
            "color_scheme": "supersetColors",
            "rich_tooltip": True,
            "show_bar_value": False,
            "adhoc_filters": [{"clause": "WHERE", "expressionType": "SIMPLE", "subject": "status_kelulusan", "operator": "IS NOT NULL", "comparator": None, "filterOptionName": "filter_not_null"}],
        }
    },
    {
        "name": "Status Mahasiswa per Angkatan",
        "viz_type": "echarts_timeseries_bar",
        "params": {
            "x_axis": "angkatan",
            "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(DISTINCT id_mahasiswa)", "label": "Jumlah"}],
            "groupby": ["status_mahasiswa"],
            "row_limit": 100,
            "stack": True,
            "show_legend": True,
            "orientation": "vertical",
            "color_scheme": "supersetColors",
            "rich_tooltip": True,
            "show_bar_value": False,
        }
    },
    {
        "name": "Distribusi Jenis Kelamin",
        "viz_type": "pie",
        "params": {
            "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(DISTINCT id_mahasiswa)", "label": "Jumlah"},
            "groupby": ["jenis_kelamin"],
            "row_limit": 100,
            "show_labels": True,
            "label_type": "key_percent",
            "number_format": ",.0f",
            "show_legend": True,
            "color_scheme": "supersetColors",
        }
    },
    # Academic metrics
    {
        "name": "Rata-rata IPK per Angkatan",
        "viz_type": "echarts_bar",
        "params": {
            "x_axis": "angkatan",
            "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ipk), 2)", "label": "Rata-rata IPK"}],
            "row_limit": 100,
            "show_legend": True,
            "rich_tooltip": True,
            "x_axis_title": "Angkatan",
            "y_axis_title": "IPK",
            "y_axis_format": ",.2f",
            "color_scheme": "supersetColors",
        }
    },
    {
        "name": "Rata-rata IP per Angkatan",
        "viz_type": "echarts_bar",
        "params": {
            "x_axis": "angkatan",
            "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ip), 2)", "label": "Rata-rata IP"}],
            "row_limit": 100,
            "show_legend": True,
            "rich_tooltip": True,
            "x_axis_title": "Angkatan",
            "y_axis_title": "IP",
            "y_axis_format": ",.2f",
            "color_scheme": "supersetColors",
        }
    },
    {
        "name": "Rata-rata Total SKS per Angkatan",
        "viz_type": "echarts_bar",
        "params": {
            "x_axis": "angkatan",
            "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(total_sks), 1)", "label": "Rata-rata Total SKS"}],
            "row_limit": 100,
            "show_legend": True,
            "rich_tooltip": True,
            "x_axis_title": "Angkatan",
            "y_axis_title": "Total SKS",
            "y_axis_format": ",.0f",
            "color_scheme": "supersetColors",
        }
    },
    {
        "name": "Rata-rata Selisih SKS per Angkatan",
        "viz_type": "echarts_bar",
        "params": {
            "x_axis": "angkatan",
            "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(selisih_sks), 1)", "label": "Rata-rata Selisih SKS"}],
            "row_limit": 100,
            "show_legend": True,
            "rich_tooltip": True,
            "x_axis_title": "Angkatan",
            "y_axis_title": "Selisih SKS",
            "y_axis_format": ",.0f",
            "color_scheme": "supersetColors",
        }
    },
]

# Create all charts
new_chart_ids = []
for config in charts_config:
    chart = Slice(
        slice_name=config["name"],
        viz_type=config["viz_type"],
        datasource_id=DATASET_ID,
        datasource_type="table",
        params=json.dumps(config["params"]),
    )
    db.session.add(chart)
    db.session.flush()
    new_chart_ids.append(chart.id)
    print(f"  Created: {config['name']} (ID={chart.id})")

db.session.commit()
print(f"\nCreated {len(new_chart_ids)} charts")

# ============================================================
# Step 3: Build new dashboard layout
# ============================================================
print(f"\nBuilding new dashboard layout...")

position = {
    "DASHBOARD_VERSION_KEY": "DASHBOARD_VERSION_KEY",
    "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
    "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
    "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID", "meta": {"text": "Dashboard Akademik Mahasiswa"}},
}

row_id = 0
chart_row = []

for i, cid in enumerate(new_chart_ids):
    # KPIs (first 8) in row of 4
    if i < 8:
        width = 3
        height = 8
    else:
        width = 6
        height = 50

    component_id = f"CHART-{cid}"
    position[component_id] = {
        "type": "CHART",
        "id": component_id,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", f"ROW-{row_id}"],
        "meta": {
            "width": width,
            "height": height,
            "chartId": cid,
        }
    }
    chart_row.append(component_id)

    # KPIs: rows of 4
    if i < 8 and len(chart_row) == 4:
        row_id += 1
        position[f"ROW-{row_id}"] = {
            "type": "ROW",
            "id": f"ROW-{row_id}",
            "children": chart_row,
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"}
        }
        position["GRID_ID"]["children"].append(f"ROW-{row_id}")
        chart_row = []
    # Charts: rows of 2
    elif i >= 8 and len(chart_row) == 2:
        row_id += 1
        position[f"ROW-{row_id}"] = {
            "type": "ROW",
            "id": f"ROW-{row_id}",
            "children": chart_row,
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"}
        }
        position["GRID_ID"]["children"].append(f"ROW-{row_id}")
        chart_row = []

# Add remaining charts
if chart_row:
    row_id += 1
    position[f"ROW-{row_id}"] = {
        "type": "ROW",
        "id": f"ROW-{row_id}",
        "children": chart_row,
        "parents": ["ROOT_ID", "GRID_ID"],
        "meta": {"background": "BACKGROUND_TRANSPARENT"}
    }
    position["GRID_ID"]["children"].append(f"ROW-{row_id}")

dashboard.position_json = json.dumps(position)
db.session.commit()
print(f"Dashboard layout updated with {len(new_chart_ids)} charts")

# ============================================================
# Step 4: Validate
# ============================================================
print(f"\n{'='*70}")
print(f"VALIDATION")
print(f"{'='*70}")

# Reload dashboard
dashboard = db.session.query(Dashboard).get(4)
position = json.loads(dashboard.position_json)
chart_refs = [v.get("meta", {}).get("chartId") for k, v in position.items() if k.startswith("CHART-")]

print(f"Dashboard: {dashboard.dashboard_title}")
print(f"Chart references: {len(chart_refs)}")

all_valid = True
for cid in chart_refs:
    chart = db.session.query(Slice).get(cid)
    if chart:
        ds = db.session.query(SqlaTable).get(chart.datasource_id)
        print(f"  ID={cid} Name={chart.slice_name} Dataset={ds.table_name if ds else 'NONE'}")
    else:
        print(f"  ID={cid} NOT FOUND")
        all_valid = False

print(f"\nAll charts valid: {all_valid}")
print(f"\nURL: http://localhost:8088/superset/dashboard/4/")
print("\nDONE.")
