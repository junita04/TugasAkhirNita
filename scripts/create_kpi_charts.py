"""
Create missing KPI charts and add to dashboard.
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

print("=" * 70)
print("CREATE MISSING KPI CHARTS")
print("=" * 70)

# Dataset ID for dim_mahasiswa = 27
DATASET_ID = 27

# Check existing charts
existing = db.session.query(Slice).filter(Slice.slice_name.in_([
    "Rata-rata IPK", "Rata-rata IP", "Rata-rata Total SKS"
])).all()
existing_names = {c.slice_name: c.id for c in existing}
print(f"Existing KPI charts: {existing_names}")

# Create missing KPIs
kpis = [
    {
        "name": "Rata-rata IPK",
        "sql": "AVG(ipk)",
        "format": ",.2f",
    },
    {
        "name": "Rata-rata IP",
        "sql": "AVG(ip)",
        "format": ",.2f",
    },
    {
        "name": "Rata-rata Total SKS",
        "sql": "AVG(total_sks)",
        "format": ",.0f",
    },
]

new_chart_ids = []
for kpi in kpis:
    if kpi["name"] not in existing_names:
        params = {
            "metric": {
                "expressionType": "SQL",
                "sqlExpression": kpi["sql"],
                "label": kpi["sql"]
            },
            "header_font_size": 0.4,
            "subheader_font_size": 0.15,
            "y_axis_format": kpi["format"],
            "time_grain_sqla": "P1D",
            "header_color": "#000000"
        }
        
        chart = Slice(
            slice_name=kpi["name"],
            viz_type="big_number_total",
            datasource_id=DATASET_ID,
            datasource_type="table",
            params=json.dumps(params),
        )
        db.session.add(chart)
        db.session.commit()
        new_chart_ids.append(chart.id)
        print(f"  Created: {kpi['name']} (ID={chart.id})")
    else:
        new_chart_ids.append(existing_names[kpi["name"]])
        print(f"  Exists: {kpi['name']} (ID={existing_names[kpi['name']]})")

# Update dashboard layout with new KPIs
dashboard = db.session.query(Dashboard).get(4)
if dashboard:
    position = json.loads(dashboard.position_json)
    
    # Add new KPI charts to the first row
    row1 = position.get("ROW-1", {})
    if row1:
        existing_children = row1.get("children", [])
        for cid in new_chart_ids:
            component_id = f"CHART-{cid}"
            position[component_id] = {
                "type": "CHART",
                "id": component_id,
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", "ROW-1"],
                "meta": {
                    "width": 3,
                    "height": 8,
                    "chartId": cid,
                }
            }
            existing_children.append(component_id)
        row1["children"] = existing_children
        position["ROW-1"] = row1
    
    dashboard.position_json = json.dumps(position)
    db.session.commit()
    print(f"\nUpdated dashboard with new KPI charts")

print(f"\nDashboard URL: http://localhost:8088/superset/dashboard/4/")
print("\nDONE.")
