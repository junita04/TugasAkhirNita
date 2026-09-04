"""
Verify Dashboard Akademik Mahasiswa.
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
print("DASHBOARD VERIFICATION")
print("=" * 70)

# Get dashboard
dashboard = db.session.query(Dashboard).get(4)
if dashboard:
    print(f"\nDashboard: {dashboard.dashboard_title}")
    print(f"ID: {dashboard.id}")
    print(f"Published: {dashboard.published}")
    print(f"URL: http://localhost:8088/superset/dashboard/{dashboard.id}/")
    
    # Parse position_json
    position = json.loads(dashboard.position_json) if dashboard.position_json else {}
    
    # Count charts
    chart_count = sum(1 for k in position if k.startswith("CHART-"))
    print(f"\nCharts in layout: {chart_count}")
    
    # List chart IDs
    chart_ids = []
    for k, v in position.items():
        if k.startswith("CHART-"):
            chart_id = v.get("meta", {}).get("chartId")
            if chart_id:
                chart_ids.append(chart_id)
    
    # Get chart details
    print(f"\nChart details:")
    for cid in chart_ids:
        chart = db.session.query(Slice).get(cid)
        if chart:
            print(f"  ID={cid} Name={chart.slice_name} Type={chart.viz_type}")
else:
    print("Dashboard not found")

# Verify data counts
print("\n" + "=" * 70)
print("DATA VERIFICATION")
print("=" * 70)

# Check dim_mahasiswa dataset
from superset.connectors.sqla.models import SqlaTable
ds = db.session.query(SqlaTable).filter(SqlaTable.table_name == "dim_mahasiswa").first()
if ds:
    print(f"\nDataset: {ds.table_name}")
    print(f"Schema: {ds.schema}")
    print(f"Database: {ds.database.database_name}")
    
    # Get column count
    columns = ds.columns
    print(f"Columns: {len(columns)}")
    for col in columns:
        print(f"  {col.column_name} ({col.type})")

print("\nDONE.")
