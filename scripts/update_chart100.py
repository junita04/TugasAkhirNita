"""
Update chart 100 to use bar chart with virtual dataset 18
"""
import requests, json

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

# Bar chart params
bar_params = {
    "viz_type": "echarts_timeseries_bar",
    "x_axis": "rentang_ipk",
    "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "jumlah_mahasiswa"}, "label": "Jumlah Mahasiswa"}],
    "groupby": [],
    "row_limit": 10,
    "show_legend": False,
    "rich_tooltip": True,
    "stack": False,
    "color_scheme": "supersetCategory10",
    "truncate_metric": True,
    "show_bar_value": True,
}

bar_qc = {
    "datasource": {"id": 18, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "jumlah_mahasiswa"}, "label": "Jumlah Mahasiswa"}],
        "columns": ["rentang_ipk"],
    }],
    "form_data": bar_params,
    "result_format": "json",
    "result_type": "full",
}

# Test bar chart query
r = s.post(f"{BASE}/api/v1/chart/data", json=bar_qc)
print(f"Bar chart test: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if "result" in data and data["result"]:
        d = data["result"][0].get("data", [])
        print(f"Data: {d}")
        
        # Update chart 100
        r_put = s.put(f"{BASE}/api/v1/chart/100", json={
            "params": json.dumps(bar_params),
            "viz_type": "echarts_timeseries_bar",
            "datasource_id": 18,
            "datasource_type": "table",
            "query_context": json.dumps(bar_qc),
        })
        print(f"Update chart 100: {r_put.status_code}")
        if r_put.status_code == 200:
            print("Chart 100 updated successfully!")
        else:
            print(f"Error: {r_put.text[:300]}")
else:
    try:
        print(f"Error: {r.json()}")
    except:
        print(f"Error: {r.text[:300]}")
