"""
FULL SUPERSET REBUILD - DELETE AND REBUILD FROM ZERO
Uses dataset 27 (dim_mahasiswa) and 28 (fact_khs) which Trino CAN see.
"""
import sys
sys.path.insert(0, '/app')
from superset.app import create_app
from superset import db
from datetime import datetime
import json

app = create_app()
app.app_context().push()

from superset.models.dashboard import Dashboard
from superset.models.slice import Slice
from superset.connectors.sqla.models import SqlaTable

print("=" * 70)
print("STEP 1: DELETE DASHBOARD 4 AND ALL ITS CHARTS")
print("=" * 70)

# Get dashboard 4
dash = db.session.query(Dashboard).get(4)
if dash:
    pos = json.loads(dash.position_json) if dash.position_json else {}
    chart_ids = [v.get("meta", {}).get("chartId") for k, v in pos.items() if k.startswith("CHART-")]
    
    # Delete charts
    for cid in chart_ids:
        s = db.session.query(Slice).get(cid)
        if s:
            db.session.delete(s)
            print(f"  Deleted chart: {cid} ({s.slice_name})")
    
    # Delete dashboard
    db.session.delete(dash)
    db.session.commit()
    print(f"  Deleted dashboard: 4 ({dash.dashboard_title})")
else:
    print("  Dashboard 4 not found")

# Also delete any orphan slices that were created by us
orphan_names = [
    "Total Mahasiswa", "Mahasiswa Aktif", "Mahasiswa Lulus",
    "Tepat Waktu", "Terlambat", "Rata-rata IPK", "Rata-rata IP",
    "Rata-rata Total SKS", "Distribusi Mahasiswa per Angkatan",
    "Distribusi Status Mahasiswa", "Distribusi Status Kelulusan",
    "Status Kelulusan per Angkatan", "Status Mahasiswa per Angkatan",
    "Distribusi Jenis Kelamin", "Rata-rata IPK per Angkatan",
    "Rata-rata IP per Angkatan", "Rata-rata Total SKS per Angkatan",
    "Rata-rata Selisih SKS per Angkatan",
]
for name in orphan_names:
    slices = db.session.query(Slice).filter(Slice.slice_name == name).all()
    for s in slices:
        db.session.delete(s)
        print(f"  Deleted orphan: {s.id} ({s.slice_name})")

db.session.commit()

print(f"\nRemaining dashboards: {db.session.query(Dashboard).count()}")
print(f"Remaining slices: {db.session.query(Slice).count()}")

print("\n" + "=" * 70)
print("STEP 2: CREATE NEW DASHBOARD")
print("=" * 70)

new_dash = Dashboard(
    dashboard_title="Dashboard Akademik Mahasiswa",
    slug="dashboard-akademik-mahasiswa",
    published=True,
    json_metadata=json.dumps({
        "timed_refresh_immune_slices": [],
        "expanded_slices": {},
        "refresh_frequency": 0,
        "default_filters": "{}",
        "color_scheme": "supersetColors",
    }),
)
db.session.add(new_dash)
db.session.commit()
DASHBOARD_ID = new_dash.id
print(f"  Created dashboard: ID={DASHBOARD_ID}")

print("\n" + "=" * 70)
print("STEP 3: CREATE CHARTS WITH QUERY_CONTEXT")
print("=" * 70)

DS_ID = 27  # dim_mahasiswa

charts_config = [
    # KPIs
    {"name": "Total Mahasiswa", "viz": "big_number_total",
     "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total"},
     "qc_cols": [], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total"}]},
    
    {"name": "Mahasiswa Aktif", "viz": "big_number_total",
     "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN status_mahasiswa='AKTIF' THEN 1 END)", "label": "Aktif"},
     "qc_cols": [], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN status_mahasiswa='AKTIF' THEN 1 END)", "label": "Aktif"}]},
    
    {"name": "Mahasiswa Lulus", "viz": "big_number_total",
     "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN status_mahasiswa='Lulus' THEN 1 END)", "label": "Lulus"},
     "qc_cols": [], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN status_mahasiswa='Lulus' THEN 1 END)", "label": "Lulus"}]},
    
    {"name": "Tepat Waktu", "viz": "big_number_total",
     "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN label=0 THEN 1 END)", "label": "TW"},
     "qc_cols": [], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN label=0 THEN 1 END)", "label": "TW"}]},
    
    {"name": "Terlambat", "viz": "big_number_total",
     "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN label=1 THEN 1 END)", "label": "TL"},
     "qc_cols": [], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(CASE WHEN label=1 THEN 1 END)", "label": "TL"}]},
    
    {"name": "Rata-rata IPK", "viz": "big_number_total",
     "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ipk),2)", "label": "AVG_IPK"},
     "qc_cols": [], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ipk),2)", "label": "AVG_IPK"}]},
    
    {"name": "Rata-rata IP", "viz": "big_number_total",
     "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ip),2)", "label": "AVG_IP"},
     "qc_cols": [], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ip),2)", "label": "AVG_IP"}]},
    
    {"name": "Rata-rata Total SKS", "viz": "big_number_total",
     "metric": {"expressionType": "SQL", "sqlExpression": "ROUND(AVG(total_sks),1)", "label": "AVG_SKS"},
     "qc_cols": [], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(total_sks),1)", "label": "AVG_SKS"}]},
    
    # Bar/Pie charts
    {"name": "Distribusi per Angkatan", "viz": "echarts_timeseries_bar",
     "x_axis": "angkatan",
     "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
     "qc_cols": ["angkatan"], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}]},
    
    {"name": "Distribusi Jenis Kelamin", "viz": "pie",
     "groupby": ["jenis_kelamin"],
     "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"},
     "qc_cols": ["jenis_kelamin"], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}]},
    
    {"name": "Distribusi Status Mahasiswa", "viz": "pie",
     "groupby": ["status_mahasiswa"],
     "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"},
     "qc_cols": ["status_mahasiswa"], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}]},
    
    {"name": "Status Kelulusan", "viz": "pie",
     "groupby": ["status_kelulusan"],
     "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"},
     "adhoc_filters": [{"clause": "WHERE", "expressionType": "SIMPLE", "subject": "status_kelulusan", "operator": "IS NOT NULL", "comparator": None, "filterOptionName": "f1"}],
     "qc_cols": ["status_kelulusan"], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
     "qc_filters": [{"clause": "WHERE", "expressionType": "SIMPLE", "subject": "status_kelulusan", "operator": "IS NOT NULL", "comparator": None, "filterOptionName": "f1"}]},
    
    {"name": "Angkatan vs Status Kelulusan", "viz": "echarts_timeseries_bar",
     "x_axis": "angkatan",
     "groupby": ["status_kelulusan"],
     "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
     "adhoc_filters": [{"clause": "WHERE", "expressionType": "SIMPLE", "subject": "status_kelulusan", "operator": "IS NOT NULL", "comparator": None, "filterOptionName": "f1"}],
     "qc_cols": ["angkatan", "status_kelulusan"], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
     "qc_filters": [{"clause": "WHERE", "expressionType": "SIMPLE", "subject": "status_kelulusan", "operator": "IS NOT NULL", "comparator": None, "filterOptionName": "f1"}]},
    
    {"name": "Angkatan vs Status Mahasiswa", "viz": "echarts_timeseries_bar",
     "x_axis": "angkatan",
     "groupby": ["status_mahasiswa"],
     "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
     "qc_cols": ["angkatan", "status_mahasiswa"], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}]},
    
    {"name": "Rata-rata IPK per Angkatan", "viz": "echarts_bar",
     "x_axis": "angkatan",
     "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ipk),2)", "label": "Rata-rata IPK"}],
     "qc_cols": ["angkatan"], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ipk),2)", "label": "Rata-rata IPK"}]},
    
    {"name": "Rata-rata IP per Angkatan", "viz": "echarts_bar",
     "x_axis": "angkatan",
     "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ip),2)", "label": "Rata-rata IP"}],
     "qc_cols": ["angkatan"], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(ip),2)", "label": "Rata-rata IP"}]},
    
    {"name": "Rata-rata Total SKS per Angkatan", "viz": "echarts_bar",
     "x_axis": "angkatan",
     "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(total_sks),1)", "label": "Rata-rata SKS"}],
     "qc_cols": ["angkatan"], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(total_sks),1)", "label": "Rata-rata SKS"}]},
    
    {"name": "Rata-rata Selisih SKS per Angkatan", "viz": "echarts_bar",
     "x_axis": "angkatan",
     "metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(selisih_sks),1)", "label": "Rata-rata Selisih"}],
     "qc_cols": ["angkatan"], "qc_metrics": [{"expressionType": "SQL", "sqlExpression": "ROUND(AVG(selisih_sks),1)", "label": "Rata-rata Selisih"}]},
]

chart_ids = []
for cfg in charts_config:
    # Build params
    params = {"viz_type": cfg["viz"]}
    if "metric" in cfg:
        params["metric"] = cfg["metric"]
    if "metrics" in cfg:
        params["metrics"] = cfg["metrics"]
    if "x_axis" in cfg:
        params["x_axis"] = cfg["x_axis"]
    if "groupby" in cfg:
        params["groupby"] = cfg["groupby"]
    if "adhoc_filters" in cfg:
        params["adhoc_filters"] = cfg["adhoc_filters"]
    
    # Common chart settings
    if cfg["viz"] == "big_number_total":
        params["header_font_size"] = 0.4
        params["subheader_font_size"] = 0.15
        params["y_axis_format"] = ",.0f"
    elif cfg["viz"] == "pie":
        params["show_labels"] = True
        params["label_type"] = "key_percent"
        params["number_format"] = ",.0f"
        params["show_legend"] = True
        params["color_scheme"] = "supersetColors"
    elif "bar" in cfg["viz"]:
        params["show_legend"] = True
        params["rich_tooltip"] = True
        params["color_scheme"] = "supersetColors"
        params["row_limit"] = 100
    
    # Build query_context
    qc_filters = cfg.get("qc_filters", [])
    query_context = {
        "datasource": {"id": DS_ID, "type": "table"},
        "force": False,
        "queries": [{
            "columns": cfg["qc_cols"],
            "metrics": cfg["qc_metrics"],
            "row_limit": 10000,
            "time_range": "No filter",
            "filters": qc_filters,
            "extras": {},
        }],
        "result_format": "json",
        "result_type": "full",
    }
    
    chart = Slice(
        slice_name=cfg["name"],
        viz_type=cfg["viz"],
        datasource_id=DS_ID,
        datasource_type="table",
        params=json.dumps(params),
        query_context=json.dumps(query_context),
    )
    db.session.add(chart)
    db.session.flush()
    chart_ids.append(chart.id)
    print(f"  Created: {cfg['name']} (ID={chart.id})")

db.session.commit()
print(f"\nTotal charts created: {len(chart_ids)}")

print("\n" + "=" * 70)
print("STEP 4: BUILD DASHBOARD LAYOUT")
print("=" * 70)

position = {
    "DASHBOARD_VERSION_KEY": "DASHBOARD_VERSION_KEY",
    "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
    "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
    "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID", "meta": {"text": "Dashboard Akademik Mahasiswa"}},
}

row_id = 0
chart_row = []

for i, cid in enumerate(chart_ids):
    if i < 8:
        w, h = 3, 8
    else:
        w, h = 6, 50
    
    comp_id = f"CHART-{cid}"
    position[comp_id] = {
        "type": "CHART", "id": comp_id, "children": [],
        "parents": ["ROOT_ID", "GRID_ID", f"ROW-{row_id}"],
        "meta": {"width": w, "height": h, "chartId": cid}
    }
    chart_row.append(comp_id)
    
    if i < 8 and len(chart_row) == 4:
        row_id += 1
        position[f"ROW-{row_id}"] = {
            "type": "ROW", "id": f"ROW-{row_id}", "children": chart_row,
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"}
        }
        position["GRID_ID"]["children"].append(f"ROW-{row_id}")
        chart_row = []
    elif i >= 8 and len(chart_row) == 2:
        row_id += 1
        position[f"ROW-{row_id}"] = {
            "type": "ROW", "id": f"ROW-{row_id}", "children": chart_row,
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"}
        }
        position["GRID_ID"]["children"].append(f"ROW-{row_id}")
        chart_row = []

if chart_row:
    row_id += 1
    position[f"ROW-{row_id}"] = {
        "type": "ROW", "id": f"ROW-{row_id}", "children": chart_row,
        "parents": ["ROOT_ID", "GRID_ID"],
        "meta": {"background": "BACKGROUND_TRANSPARENT"}
    }
    position["GRID_ID"]["children"].append(f"ROW-{row_id}")

dashboard = db.session.query(Dashboard).get(DASHBOARD_ID)
dashboard.position_json = json.dumps(position)
db.session.commit()
print(f"  Dashboard layout saved with {len(chart_ids)} charts")

print("\n" + "=" * 70)
print("STEP 5: VALIDATE ALL CHARTS")
print("=" * 70)

import requests
import time

SUPERSET = "http://localhost:8088"
r = requests.post(f"{SUPERSET}/api/v1/security/login", json={
    "username": "admin", "password": "change-me", "provider": "db", "refresh": True
})
token = r.json().get("access_token")

all_pass = True
for cid in chart_ids:
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{SUPERSET}/api/v1/chart/{cid}/data/", headers=headers, params={"force": "true"})
    chart = db.session.query(Slice).get(cid)
    name = chart.slice_name if chart else "?"
    
    if r.status_code == 200:
        data = r.json()
        if "result" in data and isinstance(data["result"], list) and len(data["result"]) > 0:
            row_count = len(data["result"][0].get("data", []))
            print(f"  PASS: Chart {cid:3d} ({name:35s}) rows={row_count}")
        else:
            print(f"  FAIL: Chart {cid:3d} ({name:35s}) empty result")
            all_pass = False
    else:
        error = r.text[:80] if r.text else "no msg"
        print(f"  FAIL: Chart {cid:3d} ({name:35s}) HTTP {r.status_code}: {error}")
        all_pass = False

print(f"\n{'='*70}")
print(f"ALL CHARTS VALID: {all_pass}")
print(f"DASHBOARD URL: http://localhost:8088/superset/dashboard/{DASHBOARD_ID}/")
print(f"{'='*70}")
