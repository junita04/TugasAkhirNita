"""
Revert Classification Report back to table chart
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

# Revert to table chart
params = {
    "viz_type": "table",
    "all_columns": ["class", "precision", "recall", "f1_score", "support"],
    "metrics": [],
    "groupby": [],
    "order_desc": True,
    "row_limit": 10,
    "page_length": 10,
    "include_search": False,
    "show_cell_bars": True,
    "color_pn": True,
}

qc = {
    "datasource": {"id": 10, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [],
        "columns": ["class", "precision", "recall", "f1_score", "support"],
        "filters": [{"col": "class", "op": "!=", "val": "weighted_avg"}],
    }],
    "form_data": params,
    "result_format": "json",
    "result_type": "full",
}

# Test
r = s.post(f"{BASE}/api/v1/chart/data", json=qc)
print(f"API test: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    rc = data["result"][0].get("rowcount", 0) if data.get("result") else 0
    d = data["result"][0].get("data", []) if data.get("result") else []
    print(f"Rows: {rc}")
    for row in d:
        print(f"  {row}")

# Update chart
s.put(f"{BASE}/api/v1/chart/86", json={
    "params": json.dumps(params),
    "viz_type": "table",
    "query_context": json.dumps(qc),
})
print("Chart 86: reverted to table")
