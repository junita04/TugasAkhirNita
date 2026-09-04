"""
Create Dashboard Akademik Mahasiswa using Flask app context.
This approach bypasses CSRF issues.
"""
import sys
sys.path.insert(0, '/opt/airflow')

from superset.app import create_app
from superset import db
from superset.models.dashboard import Dashboard
from superset.models.slice import Slice
from superset.models.sql_lab import Query
from datetime import datetime

app = create_app()

with app.app_context():
    print("=" * 70)
    print("CREATE DASHBOARD AKADEMIK MAHASISWA")
    print("=" * 70)
    
    # Check existing dashboards
    dashboards = db.session.query(Dashboard).all()
    print(f"\nExisting dashboards: {len(dashboards)}")
    for d in dashboards:
        print(f"  ID={d.id} Title={d.dashboard_title}")
    
    # Check existing charts
    charts = db.session.query(Slice).all()
    print(f"\nExisting charts: {len(charts)}")
    
    # Find relevant charts
    relevant_names = [
        "Total Mahasiswa",
        "Mahasiswa Aktif",
        "Mahasiswa Lulus",
        "Tepat Waktu (Aktual)",
        "Terlambat (Aktual)",
        "Jumlah Mahasiswa per Angkatan",
        "Distribusi Jenis Kelamin",
        "Distribusi Status Mahasiswa",
        "Status Kelulusan Aktual (Tepat Waktu vs Terlambat)",
        "Status Kelulusan per Angkatan (Stacked)",
        "Persentase Tepat Waktu per Angkatan",
        "Rata-rata IPK per Angkatan (Lulus)",
        "Rata-rata Total SKS per Angkatan (Lulus)",
        "Rata-rata Selisih SKS per Angkatan (Lulus)",
        "Rata-rata Lama Studi per Angkatan (Lulus)",
    ]
    
    chart_ids = []
    for name in relevant_names:
        chart = db.session.query(Slice).filter(Slice.slice_name == name).first()
        if chart:
            chart_ids.append(chart.id)
            print(f"  Found: {name} (ID={chart.id})")
        else:
            print(f"  NOT FOUND: {name}")
    
    # Check if dashboard already exists
    existing_dash = db.session.query(Dashboard).filter(
        Dashboard.dashboard_title == "Dashboard Akademik Mahasiswa"
    ).first()
    
    if existing_dash:
        print(f"\nDashboard already exists: ID={existing_dash.id}")
        dashboard_id = existing_dash.id
    else:
        # Create new dashboard
        new_dash = Dashboard(
            dashboard_title="Dashboard Akademik Mahasiswa",
            slug="dashboard-akademik-mahasiswa",
            published=True,
            json_metadata='{"timed_refresh_immune_slices":[],"expanded_slices":{},"refresh_frequency":0,"default_filters":"{}","color_scheme":"supersetColors"}',
        )
        db.session.add(new_dash)
        db.session.commit()
        dashboard_id = new_dash.id
        print(f"\nCreated dashboard: ID={dashboard_id}")
    
    # Add charts to dashboard
    if chart_ids:
        # Get the dashboard
        dashboard = db.session.query(Dashboard).get(dashboard_id)
        
        # Build position_json
        import json
        position = {
            "DASHBOARD_VERSION_KEY": "DASHBOARD_VERSION_KEY",
            "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
            "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
            "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID", "meta": {"text": "Dashboard Akademik Mahasiswa"}},
        }
        
        row_id = 0
        chart_row = []
        
        for i, cid in enumerate(chart_ids):
            # KPIs (first 5) get smaller size
            if i < 5:
                width = 4
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
            
            # Create rows
            if i < 5 and len(chart_row) == 5:
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
            elif i >= 5 and len(chart_row) == 2:
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
        print(f"\nUpdated dashboard layout with {len(chart_ids)} charts")
    
    print(f"\nDashboard URL: http://localhost:8088/superset/dashboard/{dashboard_id}/")
    print("\nDONE.")
