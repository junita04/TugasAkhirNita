import requests, json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    r0 = s.get(f"{BASE}/api/v1/security/csrf_token/")
    s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": BASE})
    return s

s = api()

# Audit chart 90 (Distribusi IPK) in detail
r = s.get(f"{BASE}/api/v1/chart/90")
c = r.json()["result"]
print("=== CHART 90: Distribusi IPK Mahasiswa Aktif ===")
print(f"viz_type: {c['viz_type']}")
print(f"datasource_id: {c['datasource_id']}")
params = json.loads(c["params"])
print(f"params: {json.dumps(params, indent=2)}")
qc_str = c.get("query_context")
if qc_str:
    qc = json.loads(qc_str)
    print(f"query_context: {json.dumps(qc, indent=2)}")
else:
    print("query_context: None")

# Test query
if qc_str:
    r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
    print(f"\nAPI test: {r2.status_code}")
    if r2.status_code == 200:
        data = r2.json()
        if "result" in data and data["result"]:
            for res in data["result"]:
                print(f"  rowcount: {res.get('rowcount', '?')}")
                if res.get("data"):
                    print(f"  first 3 rows: {res['data'][:3]}")
        else:
            print(f"  result: {data}")
    else:
        print(f"  error: {r2.text[:300]}")

# Also check what the histogram query format should be
print("\n=== Testing different histogram query formats ===")

# Format 1: Use the histogram viz properly
test_qc = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "row_limit": 50000,
        "metrics": [],
        "columns": ["ipk"],
        "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
    }],
    "form_data": {
        "viz_type": "histogram",
        "all_columns_x": ["ipk"],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}],
        "row_limit": 50000,
    },
    "result_format": "json",
    "result_type": "full",
}

r3 = s.post(f"{BASE}/api/v1/chart/data", json=test_qc)
print(f"Format 1 (histogram with columns): {r3.status_code}")
if r3.status_code == 200:
    data = r3.json()
    if "result" in data and data["result"]:
        for res in data["result"]:
            print(f"  rowcount: {res.get('rowcount', '?')}")
            if res.get("data"):
                print(f"  first 3: {res['data'][:3]}")

# Format 2: Use bar chart instead of histogram
test_qc2 = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "row_limit": 50000,
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "columns": [],
        "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
        "extras": {
            "having": "",
            "where": ""
        },
        "applied_time_extras": None,
        "columns_layout": "SERIES_BY_COLUMNS",
        "series_columns": [],
        "series_limit": 0,
        "series_limit_metric": None,
        "post_processing": [{"operation": "pivot", "options": {"index": ["ipk_bin"], "columns": [], "aggregates": {"Jumlah": {"operator": "sum"}}, "drop_missing_columns": False}}, {"operation": "rename", "options": {"columns": {"Jumlah": ""}, "level": 0, "inplace": True}}, {"operation": "flatten"}]
    }],
    "form_data": {
        "viz_type": "histogram",
        "all_columns_x": ["ipk"],
        "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}],
        "row_limit": 50000,
        "link_length": 25,
        "x_axis_label": "IPK",
        "y_axis_label": "Jumlah Mahasiswa",
        "color_scheme": "supersetColors",
        "normalized": False,
    },
    "result_format": "json",
    "result_type": "full",
}

r4 = s.post(f"{BASE}/api/v1/chart/data", json=test_qc2)
print(f"Format 2 (histogram with post_processing): {r4.status_code}")
if r4.status_code == 200:
    data = r4.json()
    if "result" in data and data["result"]:
        for res in data["result"]:
            print(f"  rowcount: {res.get('rowcount', '?')}")
            if res.get("data"):
                print(f"  first 3: {res['data'][:3]}")
