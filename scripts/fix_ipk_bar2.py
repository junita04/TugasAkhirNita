"""
Fix IPK Distribution - bar chart with correct orderby
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

# Try without orderby, or with different metric ref
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

# Try different orderby formats
formats_to_try = [
    # Format 1: no orderby
    {
        "datasource": {"id": 5, "type": "table"},
        "queries": [{
            "time_range": "No filter",
            "granularity_sqla": None,
            "row_limit": 500,
            "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
            "columns": [],
            "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
        }],
        "form_data": params_ipk,
        "result_format": "json",
        "result_type": "full",
    },
    # Format 2: orderby with label
    {
        "datasource": {"id": 5, "type": "table"},
        "queries": [{
            "time_range": "No filter",
            "granularity_sqla": None,
            "row_limit": 500,
            "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
            "columns": [],
            "orderby": [["Jumlah", False]],
            "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
        }],
        "form_data": params_ipk,
        "result_format": "json",
        "result_type": "full",
    },
]

for i, qc in enumerate(formats_to_try):
    print(f"\n--- Format {i+1} ---")
    r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
    print(f"Status: {r2.status_code}")
    if r2.status_code == 200:
        data = r2.json()
        if "result" in data and data["result"]:
            rc = data["result"][0].get("rowcount", 0)
            print(f"Row count: {rc}")
            d = data["result"][0].get("data", [])
            if d:
                print(f"Sample: {d[:3]}")
            # Update chart with this working format
            s.put(f"{BASE}/api/v1/chart/100", json={
                "params": json.dumps(params_ipk),
                "viz_type": "echarts_timeseries_bar",
                "query_context": json.dumps(qc),
            })
            print("Chart updated!")
            break
    else:
        try:
            err = r2.json()
            print(f"Error: {json.dumps(err)[:200]}")
        except:
            print(f"Error: {r2.text[:200]}")
