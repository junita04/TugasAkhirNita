"""
Deep audit - check chart params, dataset, and renderability.
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
print("DEEP CHART AUDIT")
print("=" * 70)

# Dashboard charts
dashboard = db.session.query(Dashboard).get(4)
position = json.loads(dashboard.position_json) if dashboard.position_json else {}

chart_ids = []
for key, value in position.items():
    if key.startswith("CHART-"):
        chart_id = value.get("meta", {}).get("chartId")
        if chart_id:
            chart_ids.append(chart_id)

# Audit each chart
issues = []
for cid in chart_ids:
    chart = db.session.query(Slice).get(cid)
    if not chart:
        issues.append(f"Chart {cid}: NOT FOUND")
        continue
    
    print(f"\n--- Chart ID={cid} Name={chart.slice_name} ---")
    print(f"  viz_type: {chart.viz_type}")
    print(f"  datasource_id: {chart.datasource_id}")
    print(f"  datasource_type: {chart.datasource_type}")
    
    # Check dataset
    ds = db.session.query(SqlaTable).get(chart.datasource_id)
    if ds:
        print(f"  dataset: {ds.table_name} (schema={ds.schema})")
        print(f"  database: {ds.database.database_name}")
        print(f"  columns: {len(ds.columns)}")
    else:
        print(f"  dataset: NOT FOUND (ID={chart.datasource_id})")
        issues.append(f"Chart {cid} ({chart.slice_name}): dataset NOT FOUND")
    
    # Check params
    if chart.params:
        try:
            params = json.loads(chart.params)
            print(f"  params keys: {list(params.keys())}")
            
            # Check for metric
            if "metric" in params:
                metric = params["metric"]
                if isinstance(metric, dict):
                    print(f"  metric type: {metric.get('expressionType')}")
                    print(f"  metric sql: {metric.get('sqlExpression')}")
                else:
                    print(f"  metric: {metric}")
            elif "metrics" in params:
                print(f"  metrics: {params['metrics']}")
            elif "groupby" in params:
                print(f"  groupby: {params['groupby']}")
        except json.JSONDecodeError:
            print(f"  params: INVALID JSON")
            issues.append(f"Chart {cid} ({chart.slice_name}): invalid params JSON")
    else:
        print(f"  params: EMPTY")
        issues.append(f"Chart {cid} ({chart.slice_name}): empty params")
    
    # Check query_context (for explore_json)
    if chart.query_context:
        print(f"  query_context: present")
    else:
        print(f"  query_context: EMPTY")

print(f"\n{'='*70}")
print(f"SUMMARY")
print(f"{'='*70}")
print(f"Charts checked: {len(chart_ids)}")
print(f"Issues found: {len(issues)}")
for issue in issues:
    print(f"  - {issue}")
