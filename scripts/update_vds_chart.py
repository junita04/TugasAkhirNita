"""
Update virtual dataset 18 with proper SQL and update chart 100
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

# Update dataset 18 with proper SQL
proper_sql = """
SELECT
    CASE
        WHEN ipk < 2.00 THEN '1. < 2.00'
        WHEN ipk >= 2.00 AND ipk < 2.50 THEN '2. 2.00 - 2.49'
        WHEN ipk >= 2.50 AND ipk < 3.00 THEN '3. 2.50 - 2.99'
        WHEN ipk >= 3.00 AND ipk < 3.50 THEN '4. 3.00 - 3.49'
        WHEN ipk >= 3.50 AND ipk <= 4.00 THEN '5. 3.50 - 4.00'
        ELSE '6. Tidak Valid'
    END AS rentang_ipk,
    COUNT(*) AS jumlah_mahasiswa
FROM iceberg.gold.data_referensi_mahasiswa
WHERE status_mahasiswa = 'AKTIF'
  AND ipk IS NOT NULL
  AND ipk BETWEEN 0 AND 4
GROUP BY 1
ORDER BY
    CASE
        WHEN ipk < 2.00 THEN 1
        WHEN ipk >= 2.00 AND ipk < 2.50 THEN 2
        WHEN ipk >= 2.50 AND ipk < 3.00 THEN 3
        WHEN ipk >= 3.00 AND ipk < 3.50 THEN 4
        WHEN ipk >= 3.50 AND ipk <= 4.00 THEN 5
        ELSE 6
    END
"""

print("Updating dataset 18 SQL...")
r = s.put(f"{BASE}/api/v1/dataset/18", json={"sql": proper_sql})
print(f"Update dataset: {r.status_code}")
if r.status_code != 200:
    print(f"Error: {r.text[:300]}")

# Refresh dataset columns
print("\nRefreshing dataset 18...")
r = s.put(f"{BASE}/api/v1/dataset/18/refresh", json={})
print(f"Refresh: {r.status_code}")

# Test the dataset
print("\nTesting dataset 18...")
test_qc = {
    "datasource": {"id": 18, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": ["count"],
        "columns": ["rentang_ipk", "jumlah_mahasiswa"],
    }],
    "form_data": {},
    "result_format": "json",
    "result_type": "full",
}
r = s.post(f"{BASE}/api/v1/chart/data", json=test_qc)
print(f"Test: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if "result" in data and data["result"]:
        d = data["result"][0].get("data", [])
        print(f"Data: {d}")
else:
    try:
        print(f"Error: {r.json()}")
    except:
        print(f"Error: {r.text[:300]}")

# Now update chart 100 to use bar chart with dataset 18
print("\nUpdating chart 100...")
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
else:
    try:
        print(f"Error: {r.json()}")
    except:
        print(f"Error: {r.text[:300]}")
