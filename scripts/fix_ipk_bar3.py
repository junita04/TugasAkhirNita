"""
Fix IPK Distribution - bar chart with ipk as column
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

# The x_axis in echarts_timeseries_bar should handle the grouping
# But we need to make sure ipk is in the columns or as x_axis
# Let me check what the working chart 71 does

r71 = s.get(f"{BASE}/api/v1/chart/71")
c71 = r71.json()["result"]
qc71 = json.loads(c71["query_context"])
print("Chart 71 query:")
print(json.dumps(qc71["queries"][0], indent=2))

# Now try with ipk in columns
qc = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 500,
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "columns": ["ipk"],
        "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
    }],
    "form_data": {
        "viz_type": "echarts_timeseries_bar",
        "x_axis": "ipk",
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "groupby": [],
        "row_limit": 500,
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}],
    },
    "result_format": "json",
    "result_type": "full",
}

r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
print(f"\nStatus: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    if "result" in data and data["result"]:
        rc = data["result"][0].get("rowcount", 0)
        print(f"Row count: {rc}")
        d = data["result"][0].get("data", [])
        if d:
            print(f"Sample: {d[:5]}")
            # Update chart
            s.put(f"{BASE}/api/v1/chart/100", json={
                "params": json.dumps(qc["form_data"]),
                "viz_type": "echarts_timeseries_bar",
                "query_context": json.dumps(qc),
            })
            print("Chart updated!")
else:
    try:
        err = r2.json()
        print(f"Error: {json.dumps(err)[:300]}")
    except:
        print(f"Error: {r2.text[:300]}")
