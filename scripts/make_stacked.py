"""
Convert chart 87 to stacked bar chart
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

# Update chart 87 to stacked
params = {
    "viz_type": "echarts_timeseries_bar",
    "x_axis": "angkatan",
    "metrics": [
        {
            "expressionType": "SQL",
            "sqlExpression": "MAX(prediksi_tepat_waktu)",
            "label": "Prediksi Tepat Waktu"
        },
        {
            "expressionType": "SQL",
            "sqlExpression": "MAX(prediksi_terlambat)",
            "label": "Prediksi Terlambat"
        }
    ],
    "groupby": [],
    "row_limit": 50,
    "stack": True,
    "show_legend": True,
    "orientation": "vertical",
    "color_scheme": "supersetCategory10",
    "rich_tooltip": True,
    "show_bar_value": True,
}

r = s.put(f"{BASE}/api/v1/chart/87", json={"params": json.dumps(params)})
print(f"Chart 87 updated: {r.status_code}")

# Verify
r2 = s.get(f"{BASE}/api/v1/chart/87")
c = r2.json()["result"]
p = json.loads(c.get("params", "{}"))
print(f"stack: {p.get('stack')}")
