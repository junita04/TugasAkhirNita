"""
Create Dashboard Akademik Mahasiswa with existing charts.
Focus: Academic data only, NO ML predictions.
"""
import requests
import json

SUPERSET = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "change-me"

def get_jwt_token():
    r = requests.post(f"{SUPERSET}/api/v1/security/login", json={
        "username": USERNAME, "password": PASSWORD, "provider": "db", "refresh": True
    })
    return r.json().get("access_token")

def get_csrf_token(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{SUPERSET}/api/v1/security/csrf_token/", headers=headers)
    return r.json().get("result")

def api_get(token, path):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{SUPERSET}{path}", headers=headers)
    return r.json()

def api_post(token, path, data, csrf_token=None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if csrf_token:
        headers["X-CSRFToken"] = csrf_token
    r = requests.post(f"{SUPERSET}{path}", headers=headers, json=data)
    return r

def api_put(token, path, data, csrf_token=None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if csrf_token:
        headers["X-CSRFToken"] = csrf_token
    r = requests.put(f"{SUPERSET}{path}", headers=headers, json=data)
    return r

token = get_jwt_token()
csrf = get_csrf_token(token)
print(f"JWT: OK, CSRF: {'OK' if csrf else 'NONE'}")

# ============================================================
# Step 1: Create missing KPI charts
# ============================================================
print("=== Creating missing KPI charts ===")

# Dataset ID for dim_mahasiswa = 27
DATASET_ID = 27

# Check if Rata-rata IPK KPI exists
charts = api_get(token, "/api/v1/chart/?q=(page_size:200)")
existing_names = {c["slice_name"]: c["id"] for c in charts.get("result", [])}
print(f"Existing charts: {len(existing_names)}")

# KPIs to create
kpis_to_create = []

# Rata-rata IPK
if "Rata-rata IPK" not in existing_names:
    kpis_to_create.append({
        "slice_name": "Rata-rata IPK",
        "viz_type": "big_number_total",
        "datasource_id": DATASET_ID,
        "datasource_type": "table",
        "params": json.dumps({
            "metric": {"expressionType": "SQL", "sqlExpression": "AVG(ipk)", "label": "AVG(ipk)"},
            "header_font_size": 0.4,
            "subheader_font_size": 0.15,
            "y_axis_format": ",.2f",
            "time_grain_sqla": "P1D",
            "header_color": "#000000"
        })
    })

# Rata-rata IP
if "Rata-rata IP" not in existing_names:
    kpis_to_create.append({
        "slice_name": "Rata-rata IP",
        "viz_type": "big_number_total",
        "datasource_id": DATASET_ID,
        "datasource_type": "table",
        "params": json.dumps({
            "metric": {"expressionType": "SQL", "sqlExpression": "AVG(ip)", "label": "AVG(ip)"},
            "header_font_size": 0.4,
            "subheader_font_size": 0.15,
            "y_axis_format": ",.2f",
            "time_grain_sqla": "P1D",
            "header_color": "#000000"
        })
    })

# Rata-rata Total SKS
if "Rata-rata Total SKS" not in existing_names:
    kpis_to_create.append({
        "slice_name": "Rata-rata Total SKS",
        "viz_type": "big_number_total",
        "datasource_id": DATASET_ID,
        "datasource_type": "table",
        "params": json.dumps({
            "metric": {"expressionType": "SQL", "sqlExpression": "AVG(total_sks)", "label": "AVG(total_sks)"},
            "header_font_size": 0.4,
            "subheader_font_size": 0.15,
            "y_axis_format": ",.0f",
            "time_grain_sqla": "P1D",
            "header_color": "#000000"
        })
    })

new_chart_ids = {}
for kpi in kpis_to_create:
    r = api_post(token, "/api/v1/chart/", kpi, csrf)
    if r.status_code == 200:
        chart_id = r.json().get("id")
        new_chart_ids[kpi["slice_name"]] = chart_id
        print(f"  Created: {kpi['slice_name']} (ID={chart_id})")
    else:
        print(f"  Error creating {kpi['slice_name']}: {r.status_code} {r.text[:100]}")

# ============================================================
# Step 2: Get all relevant chart IDs
# ============================================================
print("\n=== Collecting relevant charts ===")

# Refresh chart list
charts = api_get(token, "/api/v1/chart/?q=(page_size:200)")
chart_map = {c["slice_name"]: c["id"] for c in charts.get("result", [])}

# Relevant charts for Dashboard Akademik
relevant_charts = [
    # KPIs
    "Total Mahasiswa",
    "Mahasiswa Aktif",
    "Mahasiswa Lulus",
    "Tepat Waktu (Aktual)",
    "Terlambat (Aktual)",
    "Rata-rata IPK",
    "Rata-rata IP",
    "Rata-rata Total SKS",
    # Distributions
    "Jumlah Mahasiswa per Angkatan",
    "Distribusi Jenis Kelamin",
    "Distribusi Status Mahasiswa",
    "Status Kelulusan Aktual (Tepat Waktu vs Terlambat)",
    "Status Kelulusan per Angkatan (Stacked)",
    "Persentase Tepat Waktu per Angkatan",
    # Academic metrics
    "Rata-rata IPK per Angkatan (Lulus)",
    "Rata-rata Total SKS per Angkatan (Lulus)",
    "Rata-rata Selisih SKS per Angkatan (Lulus)",
    "Rata-rata Lama Studi per Angkatan (Lulus)",
]

chart_ids = []
for name in relevant_charts:
    if name in chart_map:
        chart_ids.append(chart_map[name])
        print(f"  Found: {name} (ID={chart_map[name]})")
    else:
        print(f"  NOT FOUND: {name}")

# ============================================================
# Step 3: Create new dashboard
# ============================================================
print("\n=== Creating Dashboard Akademik Mahasiswa ===")

dashboard_payload = {
    "dashboard_title": "Dashboard Akademik Mahasiswa",
    "slug": "dashboard-akademik-mahasiswa",
    "published": True,
    "position_json": json.dumps({
        "DASHBOARD_VERSION_KEY": "DASHBOARD_VERSION_KEY",
        "GRID_ID": "GRID_ID",
        "ROOT_ID": "ROOT_ID",
        "HEADER_ID": "HEADER_ID",
    }),
    "json_metadata": json.dumps({
        "timed_refresh_immune_slices": [],
        "expanded_slices": {},
        "refresh_frequency": 0,
        "default_filters": "{}",
        "color_scheme": "supersetColors",
        "label_colors": {},
        "shared_label_colors": {},
        "color_scheme_domain": [],
        "cross_filters_enabled": True,
    }),
}

r = api_post(token, "/api/v1/dashboard/", dashboard_payload, csrf)
if r.status_code == 200:
    dashboard_id = r.json().get("id")
    print(f"  Created dashboard: ID={dashboard_id}")
else:
    print(f"  Error: {r.status_code} {r.text[:200]}")
    dashboard_id = None

# ============================================================
# Step 4: Add charts to dashboard
# ============================================================
if dashboard_id and chart_ids:
    print(f"\n=== Adding {len(chart_ids)} charts to dashboard ===")
    
    # Build position_json with charts
    position = {
        "DASHBOARD_VERSION_KEY": "DASHBOARD_VERSION_KEY",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
        "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID", "meta": {"text": "Dashboard Akademik Mahasiswa"}},
    }
    
    row_id = 0
    col_id = 0
    chart_row = []
    
    for i, cid in enumerate(chart_ids):
        # KPIs get smaller size (3 columns), others get larger (6 columns)
        if i < 8:  # KPIs
            width = 3
            height = 8
        else:  # Charts
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
                "sliceName": f"Chart {cid}",
            }
        }
        
        chart_row.append(component_id)
        
        # Create rows of 4 for KPIs, 2 for charts
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
    
    # Add remaining charts to a row
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
    
    # Update dashboard
    r = api_put(token, f"/api/v1/dashboard/{dashboard_id}", {
        "position_json": json.dumps(position)
    }, csrf)
    print(f"  Updated layout: {r.status_code}")

print("\n=== DONE ===")
print(f"Dashboard ID: {dashboard_id}")
print(f"URL: {SUPERSET}/superset/dashboard/{dashboard_id}/")
