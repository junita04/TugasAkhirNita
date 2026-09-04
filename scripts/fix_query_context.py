"""
Generate query_context for all charts in Dashboard 4.
This is needed for charts to render properly.
"""
import sys
sys.path.insert(0, '/app')
from superset.app import create_app
from superset import db
import json

app = create_app()
app.app_context().push()

from superset.models.slice import Slice
from superset.connectors.sqla.models import SqlaTable
from superset.utils.core import get_example_database

print("=" * 70)
print("GENERATE QUERY_CONTEXT FOR ALL CHARTS")
print("=" * 70)

# Get dataset 27
ds = db.session.query(SqlaTable).get(27)
print(f"Dataset: {ds.table_name} (ID={ds.id})")

# Chart configs - each needs query_context
charts_to_fix = [127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144]

for cid in charts_to_fix:
    chart = db.session.query(Slice).get(cid)
    if not chart:
        print(f"  SKIP: Chart {cid} not found")
        continue
    
    params = json.loads(chart.params) if chart.params else {}
    
    # Build query_context based on viz_type
    viz_type = chart.viz_type
    
    if viz_type == "big_number_total":
        # Simple metric query
        metric = params.get("metric", {})
        query_context = {
            "datasource": {"id": ds.id, "type": "table"},
            "force": False,
            "queries": [{
                "columns": [],
                "metrics": [metric] if isinstance(metric, dict) else [],
                "row_limit": 10000,
                "time_range": "No filter",
            }],
            "result_format": "json",
            "result_type": "full",
        }
    elif viz_type == "pie":
        metric = params.get("metric", {})
        groupby = params.get("groupby", [])
        adhoc_filters = params.get("adhoc_filters", [])
        query_context = {
            "datasource": {"id": ds.id, "type": "table"},
            "force": False,
            "queries": [{
                "columns": groupby,
                "metrics": [metric] if isinstance(metric, dict) else [],
                "row_limit": 10000,
                "time_range": "No filter",
                "filters": [],
                "extras": {},
            }],
            "result_format": "json",
            "result_type": "full",
        }
    elif viz_type in ("echarts_timeseries_bar", "echarts_bar", "echarts_timeseries_line"):
        metrics = params.get("metrics", [])
        groupby = params.get("groupby", [])
        x_axis = params.get("x_axis", "")
        adhoc_filters = params.get("adhoc_filters", [])
        
        # For bar charts, x_axis column goes in columns
        columns = []
        if x_axis:
            columns.append(x_axis)
        columns.extend(groupby)
        
        query_context = {
            "datasource": {"id": ds.id, "type": "table"},
            "force": False,
            "queries": [{
                "columns": columns,
                "metrics": metrics if isinstance(metrics, list) else [],
                "row_limit": 10000,
                "time_range": "No filter",
                "filters": [],
                "extras": {},
                "orderby": [[metrics[0], False]] if metrics else [],
            }],
            "result_format": "json",
            "result_type": "full",
        }
    else:
        print(f"  SKIP: Unknown viz_type {viz_type} for chart {cid}")
        continue
    
    chart.query_context = json.dumps(query_context)
    db.session.commit()
    print(f"  FIXED: Chart {cid} ({chart.slice_name}) - query_context saved ({len(json.dumps(query_context))} bytes)")

print(f"\nDONE. All charts now have query_context.")
