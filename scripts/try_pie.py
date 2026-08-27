"""
Try pie chart for IPK distribution
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

# Try pie chart
print("Pie chart:")
qc_pie = {
    "datasource": {"id": 18, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "jumlah_mahasiswa"}, "label": "Jumlah"}],
        "columns": ["rentang_ipk"],
    }],
    "form_data": {
        "viz_type": "pie",
        "metric": {"expressionType": "SIMPLE", "column": {"column_name": "jumlah_mahasiswa"}, "label": "Jumlah"},
        "groupby": ["rentang_ipk"],
        "color_scheme": "supersetCategory10",
        "show_legend": True,
        "show_labels": True,
        "label_type": "key_value_percent",
        "donut": True,
        "innerRadius": 40,
        "outerRadius": 80,
    },
    "result_format": "json",
    "result_type": "full",
}
r = s.post(f"{BASE}/api/v1/chart/data", json=qc_pie)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if "result" in data and data["result"]:
        d = data["result"][0].get("data", [])
        print(f"Data: {d}")
        
        # Update chart 100
        r_put = s.put(f"{BASE}/api/v1/chart/100", json={
            "params": json.dumps(qc_pie["form_data"]),
            "viz_type": "pie",
            "datasource_id": 18,
            "datasource_type": "table",
            "query_context": json.dumps(qc_pie),
        })
        print(f"Update chart 100: {r_put.status_code}")
else:
    try:
        err = r.json()
        print(f"Error: {json.dumps(err)[:500]}")
    except:
        print(f"Error: {r.text[:500]}")
