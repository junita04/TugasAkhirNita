"""
Create KPI summary dataset from SQL query, then use table chart for horizontal display.
This creates a Superset dataset (metadata only, no database changes).
"""
import sys, json, requests
sys.path.insert(0, '/app')
from superset.app import create_app
app = create_app()
app.app_context().push()
from superset import db
from superset.models.slice import Slice
from superset.connectors.sqla.models import SqlaTable, TableColumn

SUPERSET = 'http://localhost:8088'
r = requests.post(f'{SUPERSET}/api/v1/security/login', json={
    'username': 'admin', 'password': 'change-me', 'provider': 'db', 'refresh': True
})
token = r.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# Check if we can use the table chart with all_columns and a simple metric
# The trick: use all_columns=["label_column"] and metric=["value_column"]
# But we need label and value as actual columns in the dataset

# Approach: Use the existing dim_mahasiswa dataset with computed columns
# Add computed columns that return the KPI label and value

dataset = db.session.query(SqlaTable).get(27)
if dataset:
    existing = {c.column_name for c in dataset.columns}
    print(f"Existing columns: {sorted(existing)}")
    
    # For horizontal KPI, we need to show label + value in one row
    # The table chart with all_columns can show multiple columns side by side
    
    # Let me check if we can use a simple metric with all_columns
    # In Superset table chart:
    # - all_columns: list of column names to display
    # - metrics: list of aggregate expressions
    # If all_columns is empty, it shows metrics as columns
    # If all_columns has items, it shows those columns + metrics
    
    # So if I set all_columns=[] and metrics=[{label: "Total Mahasiswa", sql: "COUNT(*)"}],
    # it should show a single column "Total Mahasiswa" with value 32703
    
    # The issue before was that table chart showed a warning icon
    # Let me try with proper configuration
    
    print("\nTesting table chart with proper config...")

# Test with chart 145
s = db.session.query(Slice).get(145)
if s:
    metric = {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total Mahasiswa"}
    
    # Table chart: all_columns=[], metrics=[metric]
    # This should show a single column with the metric value
    params = {
        "viz_type": "table",
        "all_columns": [],
        "metrics": [metric],
        "row_limit": 1,
        "include_search": False,
        "page_length": 0,
        "table_timestamp_format": "smart_date",
        "order_desc": True,
    }
    
    qc = {
        "datasource": {"id": 27, "type": "table"},
        "queries": [{
            "metrics": [metric],
            "row_limit": 1,
        }],
        "result_format": "json",
        "result_type": "full",
    }
    
    s.viz_type = "table"
    s.params = json.dumps(params)
    s.query_context = json.dumps(qc)
    db.session.commit()
    
    r = requests.get(f'{SUPERSET}/api/v1/chart/145/data/', headers=headers, params={'force': 'true'})
    print(f"  API: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if 'result' in data and data['result']:
            for q in data['result']:
                print(f"  colnames: {q.get('colnames')}")
                print(f"  data: {q.get('data', [])}")
                print(f"  status: {q.get('status')}")
                print(f"  error: {q.get('error')}")
    else:
        print(f"  Error: {r.text[:200]}")

# Now try: what if we use a SQL query as the table data source?
# Create a custom SQL query that returns label + value
print("\n--- Testing custom SQL approach ---")

# In Superset, we can set the table to use a SQL query instead of a table
# by setting the `sql` parameter on the dataset

# But first, let me check if the table chart works at all
# by testing with a simple metric

# Restore big_number_total for chart 145
s = db.session.query(Slice).get(145)
if s:
    params = {
        "viz_type": "big_number_total",
        "metric": {"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total Mahasiswa"},
        "header_font_size": 0.6,
        "subheader_font_size": 0.0,
        "y_axis_format": ",.0f",
    }
    s.viz_type = "big_number_total"
    s.params = json.dumps(params)
    db.session.commit()
    print("Restored chart 145 to big_number_total")
