"""
Update chart 100 to use table chart with cell bars for IPK distribution
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

# Table chart with cell bars
params = {
    "viz_type": "table",
    "all_columns": ["rentang_ipk", "jumlah_mahasiswa"],
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
    "datasource": {"id": 18, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [],
        "columns": ["rentang_ipk", "jumlah_mahasiswa"],
    }],
    "form_data": params,
    "result_format": "json",
    "result_type": "full",
}

# Test
r = s.post(f"{BASE}/api/v1/chart/data", json=qc)
print(f"Test: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if "result" in data and data["result"]:
        d = data["result"][0].get("data", [])
        print(f"Data: {d}")
        
        # Update chart 100
        r_put = s.put(f"{BASE}/api/v1/chart/100", json={
            "params": json.dumps(params),
            "viz_type": "table",
            "datasource_id": 18,
            "datasource_type": "table",
            "query_context": json.dumps(qc),
        })
        print(f"Update chart 100: {r_put.status_code}")
        if r_put.status_code == 200:
            print("SUCCESS!")
        else:
            print(f"Error: {r_put.text[:300]}")
