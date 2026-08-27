"""
Fix IPK Distribution chart - try bar chart with correct params
"""
import requests
import json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r0 = s.get(f"{BASE}/api/v1/security/csrf_token/")
    s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": BASE})
    return s

s = api()

# Get chart 100 current params
r = s.get(f"{BASE}/api/v1/chart/100")
c = r.json()["result"]
print(f"Current viz_type: {c['viz_type']}")
print(f"Current params: {c['params'][:200]}")

# Try creating a NEW chart with bar type and test it
# First, check what params work for echarts_timeseries_bar
# by looking at an existing bar chart (e.g., chart 71)
r71 = s.get(f"{BASE}/api/v1/chart/71")
c71 = r71.json()["result"]
params71 = json.loads(c71["params"])
print(f"\nChart 71 params (working bar):")
for k, v in params71.items():
    print(f"  {k}: {v}")

# Now create bar chart for IPK with same structure
params_ipk = {
    "viz_type": "echarts_timeseries_bar",
    "x_axis": "ipk",
    "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
    "groupby": [],
    "order_desc": True,
    "row_limit": 500,
    "truncate_metric": True,
    "show_legend": False,
    "rich_tooltip": True,
    "tooltipTimeFormat": "smart_date",
    "x_axis_time_format": "smart_date",
    "stack": False,
    "show_bar_value": False,
    "bar_stacked": False,
    "row_limit_viz": 500,
    "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}],
    "color_scheme": "supersetCategory10",
    "extra_form_data": {},
    "dashboards": [3],
}

# Build query_context manually
qc = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 500,
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "columns": [],
        "orderby": [["COUNT(*)", False]],
        "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
        "series_columns": [],
        "series_limit": 0,
        "series_limit_metric": None,
    }],
    "form_data": params_ipk,
    "result_format": "json",
    "result_type": "full",
}

# Update chart
r_put = s.put(f"{BASE}/api/v1/chart/100", json={
    "params": json.dumps(params_ipk),
    "viz_type": "echarts_timeseries_bar",
    "query_context": json.dumps(qc),
})
print(f"\nUpdate chart: {r_put.status_code}")
if r_put.status_code != 200:
    print(f"Error: {r_put.text[:300]}")

# Test
r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
print(f"API test: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    if "result" in data and data["result"]:
        rc = data["result"][0].get("rowcount", 0)
        print(f"Row count: {rc}")
        # Show sample
        d = data["result"][0].get("data", [])
        if d:
            print(f"Sample: {d[:3]}")
else:
    try:
        err = r2.json()
        print(f"Error: {json.dumps(err, indent=2)[:500]}")
    except:
        print(f"Error: {r2.text[:300]}")
