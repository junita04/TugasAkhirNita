"""
Full audit of Dashboard ID 4 - check all chart references.
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
print("DASHBOARD ID 4 FULL AUDIT")
print("=" * 70)

# Get dashboard
dashboard = db.session.query(Dashboard).get(4)
if not dashboard:
    print("ERROR: Dashboard ID 4 not found")
    exit(1)

print(f"\nDashboard: {dashboard.dashboard_title}")
print(f"Published: {dashboard.published}")

# Parse position_json
position = json.loads(dashboard.position_json) if dashboard.position_json else {}

# Extract all chart references from position_json
chart_refs = []
for key, value in position.items():
    if key.startswith("CHART-"):
        chart_id = value.get("meta", {}).get("chartId")
        chart_refs.append({
            "position_key": key,
            "chart_id": chart_id,
            "width": value.get("meta", {}).get("width"),
            "height": value.get("meta", {}).get("height"),
        })

print(f"\nTotal chart references in layout: {len(chart_refs)}")

# Check each chart reference
valid_charts = []
invalid_charts = []
for ref in chart_refs:
    chart_id = ref["chart_id"]
    if chart_id:
        chart = db.session.query(Slice).get(chart_id)
        if chart:
            valid_charts.append(ref)
            print(f"  VALID: {ref['position_key']} -> Chart ID={chart_id} Name={chart.slice_name}")
        else:
            invalid_charts.append(ref)
            print(f"  INVALID: {ref['position_key']} -> Chart ID={chart_id} (NOT FOUND)")
    else:
        invalid_charts.append(ref)
        print(f"  INVALID: {ref['position_key']} -> No chartId")

# Check all existing charts
print(f"\n--- All existing charts ---")
all_charts = db.session.query(Slice).all()
print(f"Total charts in Superset: {len(all_charts)}")

# Check dataset availability
print(f"\n--- Dataset availability ---")
datasets = db.session.query(SqlaTable).all()
for ds in datasets:
    print(f"  ID={ds.id} Table={ds.table_name} Schema={ds.schema} DB={ds.database.database_name}")

# Summary
print(f"\n{'='*70}")
print(f"SUMMARY")
print(f"{'='*70}")
print(f"Dashboard ID: 4")
print(f"Total chart references: {len(chart_refs)}")
print(f"Valid charts: {len(valid_charts)}")
print(f"Invalid charts: {len(invalid_charts)}")

# List invalid chart IDs
if invalid_charts:
    print(f"\nInvalid chart IDs to remove:")
    for inv in invalid_charts:
        print(f"  {inv['position_key']} (chartId={inv['chart_id']})")
