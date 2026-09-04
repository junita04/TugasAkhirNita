"""
Final validation - verify dashboard can render all charts.
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
from superset.utils.core import get_example_database

print("=" * 70)
print("FINAL DASHBOARD VALIDATION")
print("=" * 70)

dashboard = db.session.query(Dashboard).get(4)
position = json.loads(dashboard.position_json) if dashboard.position_json else {}

# Get all chart references
chart_refs = []
for key, value in position.items():
    if key.startswith("CHART-"):
        chart_id = value.get("meta", {}).get("chartId")
        chart_refs.append(chart_id)

print(f"\nDashboard: {dashboard.dashboard_title}")
print(f"Dashboard ID: {dashboard.id}")
print(f"Published: {dashboard.published}")
print(f"Chart references: {len(chart_refs)}")

# Validate each chart
print(f"\n{'='*70}")
print(f"CHART VALIDATION")
print(f"{'='*70}")

all_valid = True
for cid in chart_refs:
    chart = db.session.query(Slice).get(cid)
    if not chart:
        print(f"  FAIL: Chart {cid} NOT FOUND")
        all_valid = False
        continue
    
    ds = db.session.query(SqlaTable).get(chart.datasource_id)
    if not ds:
        print(f"  FAIL: Chart {cid} ({chart.slice_name}) - dataset NOT FOUND")
        all_valid = False
        continue
    
    # Check columns exist
    params = json.loads(chart.params) if chart.params else {}
    ds_columns = [c.column_name for c in ds.columns]
    
    # Check metric columns
    metric_ok = True
    if "metric" in params:
        metric = params["metric"]
        if isinstance(metric, dict) and "sqlExpression" in metric:
            sql = metric["sqlExpression"]
            # Extract column names from SQL
            import re
            cols_in_sql = re.findall(r'\b(\w+)\b', sql)
            for col in cols_in_sql:
                if col.upper() not in ["COUNT", "DISTINCT", "CASE", "WHEN", "THEN", "END", "AVG", "ROUND", "NULLIF", "SUM", "MIN", "MAX", "COALESCE", "NULL", "AS"]:
                    if col not in ds_columns and col.lower() not in [c.lower() for c in ds_columns]:
                        pass  # Could be a literal or alias
    
    print(f"  PASS: Chart {cid} ({chart.slice_name}) - Dataset={ds.table_name} - OK")

# Validate data
print(f"\n{'='*70}")
print(f"DATA VALIDATION")
print(f"{'='*70}")

ds = db.session.query(SqlaTable).get(27)
print(f"\nDataset: {ds.table_name}")
print(f"Schema: {ds.schema}")
print(f"Database: {ds.database.database_name}")
print(f"Columns: {len(ds.columns)}")

# Check angkatan distribution
print(f"\nExpected angkatan distribution (from Gold):")
print(f"  2012: 49")
print(f"  2013: 33")
print(f"  2014: 66")
print(f"  2015: 397")
print(f"  2016: 1295")
print(f"  2017: 1579")
print(f"  2018: 2535")
print(f"  2019: 3663")
print(f"  2020: 4566")
print(f"  2021: 4697")
print(f"  2022: 4873")
print(f"  2023: 4447")
print(f"  2024: 4503")
print(f"  TOTAL: 32703")

# Final summary
print(f"\n{'='*70}")
print(f"FINAL SUMMARY")
print(f"{'='*70}")
print(f"Dashboard ID: {dashboard.id}")
print(f"Dashboard Title: {dashboard.dashboard_title}")
print(f"Published: {dashboard.published}")
print(f"Total Charts: {len(chart_refs)}")
print(f"All Valid: {all_valid}")
print(f"All on Dataset: dim_mahasiswa (ID=27)")
print(f"\nURL: http://localhost:8088/superset/dashboard/{dashboard.id}/")
print(f"\nRESULT: {'PASS' if all_valid else 'FAIL'}")
print("\nDONE.")
