"""
Update chart 100 to use histogram plugin for IPK distribution
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

# Histogram params
hist_params = {
    "viz_type": "histogram",
    "all_columns_x": ["ipk"],
    "adhoc_filters": [
        {"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}
    ],
    "row_limit": 10000,
    "groupby": [],
    "color_scheme": "supersetCategory10",
    "link_length": 25,
    "x_axis_label": "IPK",
    "y_axis_label": "Jumlah Mahasiswa",
    "normalize": False,
    "show_legend": False,
    "extra_form_data": {},
    "dashboards": [3],
}

hist_qc = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10000,
        "metrics": [],
        "columns": ["ipk"],
        "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
    }],
    "form_data": hist_params,
    "result_format": "json",
    "result_type": "full",
}

# Update chart
r = s.put(f"{BASE}/api/v1/chart/100", json={
    "params": json.dumps(hist_params),
    "viz_type": "histogram",
    "query_context": json.dumps(hist_qc),
})
print(f"Update chart 100: {r.status_code}")

# Test
r2 = s.post(f"{BASE}/api/v1/chart/data", json=hist_qc)
print(f"API test: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    if "result" in data and data["result"]:
        rc = data["result"][0].get("rowcount", 0)
        print(f"Row count: {rc}")
        d = data["result"][0].get("data", [])
        if d:
            print(f"Sample: {d[:3]}")
    else:
        print("No result")
else:
    try:
        print(f"Error: {r2.json()}")
    except:
        print(f"Error: {r2.text[:300]}")
