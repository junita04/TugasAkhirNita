"""
Debug bar chart query error
"""
import requests, json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s

s = api()

# Try different chart types
# 1. Table chart
print("1. Table chart:")
qc_table = {
    "datasource": {"id": 18, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [],
        "columns": ["rentang_ipk", "jumlah_mahasiswa"],
    }],
    "form_data": {"viz_type": "table"},
    "result_format": "json",
    "result_type": "full",
}
r = s.post(f"{BASE}/api/v1/chart/data", json=qc_table)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if "result" in data and data["result"]:
        d = data["result"][0].get("data", [])
        print(f"  Data: {d}")

# 2. Try bar chart with correct params
print("\n2. Bar chart (corrected):")
qc_bar = {
    "datasource": {"id": 18, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "jumlah_mahasiswa"}, "label": "Jumlah Mahasiswa"}],
        "columns": [],
        "orderby": [["jumlah_mahasiswa", False]],
    }],
    "form_data": {
        "viz_type": "echarts_timeseries_bar",
        "x_axis": "rentang_ipk",
        "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "jumlah_mahasiswa"}, "label": "Jumlah Mahasiswa"}],
        "groupby": [],
    },
    "result_format": "json",
    "result_type": "full",
}
r = s.post(f"{BASE}/api/v1/chart/data", json=qc_bar)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if "result" in data and data["result"]:
        d = data["result"][0].get("data", [])
        print(f"  Data: {d}")
else:
    try:
        err = r.json()
        print(f"  Error: {json.dumps(err)[:500]}")
    except:
        print(f"  Error: {r.text[:500]}")

# 3. Try with columns in query
print("\n3. Bar chart with columns:")
qc_bar2 = {
    "datasource": {"id": 18, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "jumlah_mahasiswa"}, "label": "Jumlah Mahasiswa"}],
        "columns": ["rentang_ipk"],
        "orderby": [["jumlah_mahasiswa", False]],
    }],
    "form_data": {
        "viz_type": "echarts_timeseries_bar",
        "x_axis": "rentang_ipk",
        "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "jumlah_mahasiswa"}, "label": "Jumlah Mahasiswa"}],
        "groupby": [],
    },
    "result_format": "json",
    "result_type": "full",
}
r = s.post(f"{BASE}/api/v1/chart/data", json=qc_bar2)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if "result" in data and data["result"]:
        d = data["result"][0].get("data", [])
        print(f"  Data: {d}")
else:
    try:
        err = r.json()
        print(f"  Error: {json.dumps(err)[:500]}")
    except:
        print(f"  Error: {r.text[:500]}")
