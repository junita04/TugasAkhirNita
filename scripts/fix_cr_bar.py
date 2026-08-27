"""
Fix Classification Report - try different query formats
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

def make_metric(sql, label):
    return {"expressionType": "SQL", "sqlExpression": sql, "label": label}

s = api()

# Test different approaches for classification report
# Data: class, precision, recall, f1_score, support

# Approach 1: Use simple metrics
print("Approach 1: Simple metrics")
qc1 = {
    "datasource": {"id": 10, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": ["precision", "recall", "f1_score"],
        "columns": ["class"],
        "filters": [{"col": "class", "op": "!=", "val": "weighted_avg"}],
    }],
    "form_data": {
        "viz_type": "echarts_timeseries_bar",
        "x_axis": "class",
        "metrics": ["precision", "recall", "f1_score"],
        "groupby": [],
        "row_limit": 10,
        "show_legend": True,
        "rich_tooltip": True,
        "stack": False,
    },
    "result_format": "json",
    "result_type": "full",
}

r = s.post(f"{BASE}/api/v1/chart/data", json=qc1)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if "result" in data and data["result"]:
        rc = data["result"][0].get("rowcount", 0)
        print(f"  Rows: {rc}")
else:
    try:
        print(f"  Error: {r.json()}")
    except:
        print(f"  Error: {r.text[:300]}")

# Approach 2: Use SQL metrics
print("\nApproach 2: SQL metrics")
qc2 = {
    "datasource": {"id": 10, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [
            make_metric("precision", "Precision"),
            make_metric("recall", "Recall"),
            make_metric("f1_score", "F1 Score"),
        ],
        "columns": ["class"],
        "filters": [{"col": "class", "op": "!=", "val": "weighted_avg"}],
    }],
    "form_data": {
        "viz_type": "echarts_timeseries_bar",
        "x_axis": "class",
        "metrics": [
            make_metric("precision", "Precision"),
            make_metric("recall", "Recall"),
            make_metric("f1_score", "F1 Score"),
        ],
        "groupby": [],
        "row_limit": 10,
        "show_legend": True,
        "rich_tooltip": True,
        "stack": False,
    },
    "result_format": "json",
    "result_type": "full",
}

r = s.post(f"{BASE}/api/v1/chart/data", json=qc2)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if "result" in data and data["result"]:
        rc = data["result"][0].get("rowcount", 0)
        d = data["result"][0].get("data", [])
        print(f"  Rows: {rc}")
        if d:
            print(f"  Data: {d[:2]}")
else:
    try:
        print(f"  Error: {r.json()}")
    except:
        print(f"  Error: {r.text[:300]}")

# Approach 3: Use table chart (simpler)
print("\nApproach 3: Table chart")
qc3 = {
    "datasource": {"id": 10, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [],
        "columns": ["class", "precision", "recall", "f1_score", "support"],
        "filters": [{"col": "class", "op": "!=", "val": "weighted_avg"}],
    }],
    "form_data": {
        "viz_type": "table",
        "all_columns": ["class", "precision", "recall", "f1_score", "support"],
        "metrics": [],
        "groupby": [],
        "order_desc": True,
        "row_limit": 10,
        "page_length": 10,
        "show_cell_bars": True,
    },
    "result_format": "json",
    "result_type": "full",
}

r = s.post(f"{BASE}/api/v1/chart/data", json=qc3)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if "result" in data and data["result"]:
        rc = data["result"][0].get("rowcount", 0)
        print(f"  Rows: {rc}")
