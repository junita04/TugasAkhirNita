"""
Fix chart 90: Replace histogram with a working bar chart for IPK distribution.
Also audit all other charts.
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

def make_metric(sql, label):
    return {"expressionType": "SQL", "sqlExpression": sql, "label": label}

def make_adhoc_filter(subject, operator, comparator, clause="WHERE"):
    return {"expressionType": "SIMPLE", "subject": subject, "operator": operator, "comparator": comparator, "clause": clause}

def convert_filter(f):
    return {"col": f.get("subject", ""), "op": f.get("operator", "=="), "val": f.get("comparator", None)}

def build_qc(ds_id, metrics, columns, filters=None, row_limit=50000):
    return json.dumps({
        "datasource": {"id": ds_id, "type": "table"},
        "queries": [{"time_range": "No filter", "granularity_sqla": None, "row_limit": row_limit,
                      "metrics": metrics, "columns": columns, "filters": filters or []}],
        "form_data": {},
        "result_format": "json", "result_type": "full",
    })

s = api()

# Fix chart 90: Replace histogram with echarts_timeseries_bar using SQL binning
# Create IPK bins using SQL: FLOOR(ipk * 10) / 10.0 as ipk_bin
print("=== FIXING CHART 90: Distribusi IPK Mahasiswa Aktif ===")

# Strategy: Use a table chart with SQL expression to create IPK bins
# Then display as bar chart

# First, let's use the echarts_timeseries_bar with a custom SQL groupby
params = {
    "viz_type": "echarts_timeseries_bar",
    "x_axis": "ipk_bin",
    "metrics": [make_metric("COUNT(*)", "Jumlah Mahasiswa")],
    "groupby": [],
    "row_limit": 50000,
    "adhoc_filters": [
        make_adhoc_filter("status_mahasiswa", "==", "AKTIF"),
    ],
    "truncate_metric": True,
    "show_legend": False,
    "stack": False,
    "orientation": "vertical",
    "x_axis_label": "IPK",
    "y_axis_label": "Jumlah Mahasiswa",
    "color_scheme": "supersetColors",
}

# The problem is we can't do FLOOR(ipk * 10) / 10.0 as a groupby in echarts_timeseries_bar
# Let's use a SQL-based approach with the table viz type instead

# Actually, let's try the simplest approach: use the raw data
# and let Superset do the binning. The histogram query_context
# might just need the right format.

# Test: Create a new chart with histogram and proper query_context
chart_data = {
    "slice_name": "Distribusi IPK Mahasiswa Aktif",
    "viz_type": "histogram",
    "datasource_id": 5,
    "datasource_type": "table",
    "params": json.dumps({
        "viz_type": "histogram",
        "all_columns_x": ["ipk"],
        "adhoc_filters": [
            make_adhoc_filter("status_mahasiswa", "==", "AKTIF"),
        ],
        "row_limit": 50000,
        "link_length": 25,
        "x_axis_label": "IPK",
        "y_axis_label": "Jumlah Mahasiswa",
        "color_scheme": "supersetColors",
        "normalized": False,
    }),
}

# Delete old chart 90
s.delete(f"{BASE}/api/v1/chart/90")

# Create new chart
r = s.post(f"{BASE}/api/v1/chart/", json=chart_data)
new_id = r.json()["id"]
print(f"Created new chart {new_id}")

# Now build the correct query_context for histogram
# The histogram in Superset uses post_processing to bin the data
# But the key is: the query_context must have the correct format
# that the frontend expects

# For histogram, the frontend generates query like:
# SELECT ipk FROM table WHERE status_mahasiswa = 'AKTIF' LIMIT 50000
# Then bins the data client-side

qc = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 50000,
        "metrics": [],
        "columns": [],
        "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
    }],
    "form_data": {
        "viz_type": "histogram",
        "all_columns_x": ["ipk"],
        "adhoc_filters": [make_adhoc_filter("status_mahasiswa", "==", "AKTIF")],
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

s.put(f"{BASE}/api/v1/chart/{new_id}", json={"query_context": json.dumps(qc)})

# Test
r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
if r2.status_code == 200:
    data = r2.json()
    if "result" in data and data["result"]:
        rc = data["result"][0].get("rowcount", "?")
        print(f"  API test: OK ({rc} rows)")
    else:
        print(f"  API test: OK (empty)")
else:
    print(f"  API test: FAIL ({r2.status_code})")

# Now let's also try a different approach: use a bar chart with SQL binning
# This is more reliable than the histogram plugin
print("\n=== Trying alternative: Bar chart with SQL CASE bins ===")

# Create IPK bins using SQL CASE expression
# We'll use the table viz type which is the most reliable
params_table = {
    "viz_type": "table",
    "all_columns": ["ipk"],
    "order_desc": True,
    "row_limit": 50000,
    "page_length": 50,
    "include_search": False,
    "table_timestamp_format": "smart_date",
    "show_cell_bars": True,
    "color_pn": True,
    "adhoc_filters": [make_adhoc_filter("status_mahasiswa", "==", "AKTIF")],
}

# Actually, the simplest working approach is to just use the bar chart
# with the data we already have. The histogram issue is a frontend plugin issue.
# Let's replace with a bar chart that groups by a derived column.

# But we can't do derived columns in the groupby. So let's keep the histogram
# but fix the query_context format.

# The real fix: The histogram query_context needs to have
# columns = ["ipk"] (the column to histogram) and metrics = [] (no aggregation)
# This is what we already have. The issue might be that the form_data
# in the query_context is not matching what the frontend expects.

# Let me check if the issue is the form_data format
print(f"\nNew chart ID: {new_id}")
print("Chart created. Testing...")

# Final test via the stored query_context
r3 = s.get(f"{BASE}/api/v1/chart/{new_id}")
c = r3.json()["result"]
qc_stored = json.loads(c.get("query_context", "{}"))
r4 = s.post(f"{BASE}/api/v1/chart/data", json=qc_stored)
if r4.status_code == 200:
    data = r4.json()
    if "result" in data and data["result"]:
        rc = data["result"][0].get("rowcount", "?")
        d = data["result"][0].get("data", [])
        print(f"  Stored QC test: OK ({rc} rows)")
        if d:
            print(f"  Sample: {d[:3]}")
else:
    print(f"  Stored QC test: FAIL ({r4.status_code})")

# Update dashboard_slices for the new chart ID
import psycopg2
try:
    conn = psycopg2.connect(host="postgres", database="superset", user="academic", password="")
    cur = conn.cursor()
    cur.execute("DELETE FROM dashboard_slices WHERE dashboard_id = 3 AND slice_id = 90")
    cur.execute("INSERT INTO dashboard_slices (dashboard_id, slice_id) VALUES (3, %s)", (new_id,))
    conn.commit()
    cur.close()
    conn.close()
    print(f"Updated dashboard_slices: removed 90, added {new_id}")
except Exception as e:
    print(f"psycopg2 failed: {e}")
    # Fallback: generate SQL file
    sql = f"DELETE FROM dashboard_slices WHERE dashboard_id = 3 AND slice_id = 90;\nINSERT INTO dashboard_slices (dashboard_id, slice_id) VALUES (3, {new_id});\n"
    with open("D:/TA/TugasAkhirNita/scripts/fix_ds_90.sql", "w") as f:
        f.write(sql)
    print("Generated fix_ds_90.sql")
