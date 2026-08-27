"""
Fix chart 90: Recreate as a proper bar chart with IPK distribution.
The histogram plugin is unreliable. Use a bar chart approach instead.
"""
import requests
import json
import subprocess

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

s = api()

# First, check what chart 90 looks like now (it was deleted)
r = s.get(f"{BASE}/api/v1/chart/90")
if r.status_code == 200:
    print("Chart 90 still exists, deleting...")
    s.delete(f"{BASE}/api/v1/chart/90")
else:
    print("Chart 90 already deleted")

# Create chart 90 as a table with SQL-based IPK distribution
# We'll use the table viz type with a query that bins IPK
# Actually, the best approach is to use the bar chart (echarts_timeseries_bar)
# with the IPK column grouped by value ranges

# Since we can't do SQL expressions in groupby, let's use a different approach:
# Use the table viz type to show IPK distribution in bins

# Actually, the simplest working approach for IPK distribution:
# Create a bar chart that counts students by their IPK rounded to nearest 0.5
# We can use the SQL expression in the metric

# But echarts_timeseries_bar needs a proper x_axis column.
# The IPK is a continuous value, so we need to bin it.

# Best approach: Use a table chart that shows the raw IPK data grouped
# by a derived column. But Superset doesn't support derived columns in groupby.

# Alternative: Use the Superset built-in histogram functionality
# by creating the chart with the correct params

# Let me try creating the chart with histogram type but with the
# correct query_context that the frontend expects

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

r = s.post(f"{BASE}/api/v1/chart/", json=chart_data)
new_id = r.json()["id"]
print(f"Created chart {new_id}")

# The histogram query_context format that works:
# The key insight is that the frontend histogram plugin
# sends a query with metrics=[] and columns=[],
# then uses the all_columns_x from form_data to determine
# which column to fetch. The backend returns raw data points,
# and the frontend bins them.
#
# The "Empty query?" error happens when the frontend can't
# find the correct query configuration.
#
# The fix: The query_context must have the EXACT same structure
# that the frontend expects. Let me check what the frontend sends.

# Build the minimal query_context
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

# Test the API
r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
if r2.status_code == 200:
    data = r2.json()
    if "result" in data and data["result"]:
        rc = data["result"][0].get("rowcount", "?")
        d = data["result"][0].get("data", [])
        print(f"API test: OK ({rc} rows)")
        if d:
            print(f"Sample: {d[:5]}")
    else:
        print(f"API test: OK (result empty)")
        print(f"Full response: {json.dumps(data, indent=2)[:500]}")
else:
    try:
        err = r2.json()
        print(f"API test: FAIL ({r2.status_code})")
        print(f"Error: {json.dumps(err, indent=2)[:500]}")
    except:
        print(f"API test: FAIL ({r2.status_code}) {r2.text[:300]}")

# Update dashboard_slices
print(f"\nUpdating dashboard_slices: remove 90, add {new_id}")
sql = f"DELETE FROM dashboard_slices WHERE dashboard_id = 3 AND slice_id = 90;\nINSERT INTO dashboard_slices (dashboard_id, slice_id) VALUES (3, {new_id});\n"
with open("D:/TA/TugasAkhirNita/scripts/fix_ds_90.sql", "w") as f:
    f.write(sql)
print("Generated fix_ds_90.sql")

# Also update position_json to reference the new chart ID
r3 = s.get(f"{BASE}/api/v1/dashboard/3")
dash = r3.json()["result"]
pos = json.loads(dash.get("position_json", "{}"))
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        if meta.get("chartId") == 90:
            meta["chartId"] = new_id
            print(f"Updated position_json: {key} chartId 90 -> {new_id}")

s.put(f"{BASE}/api/v1/dashboard/3", json={"position_json": json.dumps(pos)})
print("Dashboard position_json updated")
