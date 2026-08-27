"""
Try histogram plugin for IPK distribution, with fallback approaches
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

# APPROACH 1: Try histogram plugin
print("=" * 70)
print("APPROACH 1: histogram plugin")
print("=" * 70)

hist_params = {
    "viz_type": "histogram",
    "all_columns_x": ["ipk"],
    "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}],
    "row_limit": 10000,
    "groupby": [],
    "color_scheme": "supersetCategory10",
    "link_length": 25,
    "x_axis_label": "IPK",
    "y_axis_label": "Jumlah Mahasiswa",
    "normalize": False,
    "show_legend": False,
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

r = s.post(f"{BASE}/api/v1/chart/data", json=hist_qc)
print(f"histogram API: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if "result" in data and data["result"]:
        for i, result in enumerate(data["result"]):
            rc = result.get("rowcount", "?")
            print(f"  result[{i}]: rowcount={rc}")
            d = result.get("data", [])
            if d:
                print(f"  data sample: {d[:2]}")
else:
    try:
        print(f"  Error: {r.json()}")
    except:
        print(f"  Error: {r.text[:300]}")

# APPROACH 2: Try bar chart with explicit binning via SQL
print("\n" + "=" * 70)
print("APPROACH 2: bar chart with SQL CASE for bins")
print("=" * 70)

# Use a metric that creates bins
bar_params = {
    "viz_type": "echarts_timeseries_bar",
    "x_axis": "ipk",
    "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
    "groupby": [],
    "row_limit": 500,
    "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}],
    "color_scheme": "supersetCategory10",
    "show_legend": False,
    "stack": False,
}

bar_qc = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 500,
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Jumlah"}],
        "columns": ["ipk"],
        "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
    }],
    "form_data": bar_params,
    "result_format": "json",
    "result_type": "full",
}

r = s.post(f"{BASE}/api/v1/chart/data", json=bar_qc)
print(f"bar chart API: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if "result" in data and data["result"]:
        rc = data["result"][0].get("rowcount", "?")
        print(f"  rowcount: {rc}")
else:
    try:
        print(f"  Error: {r.json()}")
    except:
        print(f"  Error: {r.text[:300]}")

# APPROACH 3: Try table with SQL CASE bins
print("\n" + "=" * 70)
print("APPROACH 3: table with SQL CASE bins")
print("=" * 70)

# Create SQL expression for IPK ranges
# CASE WHEN ipk < 0.5 THEN '0.00-0.49' WHEN ipk < 1.0 THEN '0.50-0.99' ...
# But Superset doesn't support this in groupby.
# 
# Alternative: use the table chart with groupby=ipk and show the raw distribution.
# The user wants a histogram, but the closest we can get is a bar chart.
#
# Let me try one more thing: use a custom SQL column via params

# Actually, let me check if there's a way to create a "derived" column
# in Superset that would allow SQL expressions in groupby

print("Checking if derived columns are supported...")
r = s.get(f"{BASE}/api/v1/dataset/5")
ds = r.json()["result"]
print(f"  dataset columns: {len(ds.get('columns', []))}")

# Check if we can add a computed column
# In Superset 6.0, we can use "sql" parameter in the table definition
# to create a virtual dataset with computed columns

# Let me try creating a virtual dataset with IPK bins
# via SQL expression
print("\nTrying virtual dataset approach...")
virtual_sql = """
SELECT 
    CASE 
        WHEN ipk < 0.5 THEN '0.00-0.49'
        WHEN ipk < 1.0 THEN '0.50-0.99'
        WHEN ipk < 1.5 THEN '1.00-1.49'
        WHEN ipk < 2.0 THEN '1.50-1.99'
        WHEN ipk < 2.5 THEN '2.00-2.49'
        WHEN ipk < 3.0 THEN '2.50-2.99'
        WHEN ipk < 3.5 THEN '3.00-3.49'
        ELSE '3.50-4.00'
    END AS ipk_range,
    COUNT(*) AS jumlah
FROM iceberg.gold.data_referensi_mahasiswa
WHERE status_mahasiswa = 'AKTIF'
GROUP BY 1
ORDER BY 1
"""
print(f"  Virtual SQL: {virtual_sql[:100]}...")

# This would require creating a new dataset, which the user doesn't want.
# Let's stick with the bar chart approach (333 individual IPK values).

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print("The bar chart with 333 individual IPK values is the best")
print("available option without creating new datasets.")
print("It shows the distribution of IPK values for AKTIF students.")
print("The user may need to accept this or we create a virtual dataset.")
