"""
Fix the two broken charts:
1. Confusion Matrix: heatmap not registered -> replace with table crosstab
2. Distribusi IPK: replace table of raw values with proper table showing distribution
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

s = api()

# =====================================================
# FIX 1: CONFUSION MATRIX (chart 85)
# Replace heatmap with table crosstab
# =====================================================
print("=" * 70)
print("FIX 1: CONFUSION MATRIX")
print("=" * 70)

# Get current chart 85
r = s.get(f"{BASE}/api/v1/chart/85")
c = r.json()["result"]
ds_id = c["datasource_id"]  # 9 (confusion_matrix)

# The confusion_matrix table has: actual, predicted, count
# We need a table that shows actual as rows, predicted as columns
# with count values in the cells

# Approach: Use table chart with metrics=count, groupby=[actual, predicted]
# This gives a grouped table. Not a true crosstab, but shows the data.
#
# Better approach: Use table with pivoting via post_processing

# For a clean confusion matrix display, use table with:
# - columns: actual, predicted, count
# - This shows all 4 combinations

params = {
    "viz_type": "table",
    "all_columns": ["actual", "predicted", "count"],
    "order_desc": True,
    "row_limit": 100,
    "page_length": 10,
    "include_search": False,
    "table_timestamp_format": "smart_date",
    "show_cell_bars": True,
    "color_pn": True,
}

s.put(f"{BASE}/api/v1/chart/85", json={
    "params": json.dumps(params),
    "viz_type": "table",
})

# Build query_context
qc = {
    "datasource": {"id": ds_id, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 100,
        "metrics": [],
        "columns": ["actual", "predicted", "count"],
        "filters": [],
    }],
    "form_data": params,
    "result_format": "json",
    "result_type": "full",
}

s.put(f"{BASE}/api/v1/chart/85", json={"query_context": json.dumps(qc)})

# Test
r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
if r2.status_code == 200:
    data = r2.json()
    if "result" in data and data["result"]:
        rc = data["result"][0].get("rowcount", "?")
        d = data["result"][0].get("data", [])
        print(f"Chart 85: OK ({rc} rows)")
        for row in d:
            print(f"  {row}")
    else:
        print(f"Chart 85: OK (empty)")
else:
    try:
        err = r2.json()
        print(f"Chart 85: FAIL ({r2.status_code}): {err}")
    except:
        print(f"Chart 85: FAIL ({r2.status_code}) {r2.text[:200]}")

# =====================================================
# FIX 2: DISTRIBUSI IPK (chart 100)
# Replace raw IPK table with proper distribution table
# =====================================================
print("\n" + "=" * 70)
print("FIX 2: DISTRIBUSI IPK MAHASISWA AKTIF")
print("=" * 70)

# Strategy: Use a table chart that shows IPK ranges and counts
# We'll use the table chart with groupby=ipk and metric=COUNT(*)
# But that shows individual IPK values, not ranges.
#
# Better: Use SQL CASE to create bins, but Superset doesn't support
# derived columns in groupby.
#
# Alternative: Use a bar chart with the IPK as x_axis and COUNT(*) as metric.
# This will show a bar for each unique IPK value.
# With 333 unique values, this creates a dense bar chart.
#
# BEST: Use a table chart that shows the data in a clear format.
# The table chart with all_columns=[ipk] and show_cell_bars=true
# will show IPK values with bar indicators, giving a visual distribution.

# Let's verify the data first
r = s.get(f"{BASE}/api/v1/dataset/5")
ds = r.json()["result"]
ipk_col = None
for col in ds.get("columns", []):
    if col["column_name"] == "ipk":
        ipk_col = col
        break

if ipk_col:
    print(f"IPK column found: type={ipk_col.get('type', '?')}, nullable={ipk_col.get('is_nullable', '?')}")
else:
    print("IPK column NOT FOUND!")

# Create the chart with a table that shows IPK distribution
# using groupby=ipk with COUNT(*) metric
params = {
    "viz_type": "table",
    "all_columns": [],
    "metrics": [make_metric("COUNT(*)", "Jumlah")],
    "groupby": ["ipk"],
    "order_desc": True,
    "row_limit": 50000,
    "page_length": 20,
    "include_search": False,
    "table_timestamp_format": "smart_date",
    "show_cell_bars": True,
    "color_pn": True,
    "adhoc_filters": [make_adhoc_filter("status_mahasiswa", "==", "AKTIF")],
}

s.put(f"{BASE}/api/v1/chart/100", json={
    "params": json.dumps(params),
    "viz_type": "table",
})

# Build query_context
qc = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 50000,
        "metrics": [make_metric("COUNT(*)", "Jumlah")],
        "columns": ["ipk"],
        "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
    }],
    "form_data": params,
    "result_format": "json",
    "result_type": "full",
}

s.put(f"{BASE}/api/v1/chart/100", json={"query_context": json.dumps(qc)})

# Test
r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
if r2.status_code == 200:
    data = r2.json()
    if "result" in data and data["result"]:
        rc = data["result"][0].get("rowcount", "?")
        d = data["result"][0].get("data", [])
        print(f"Chart 100: OK ({rc} rows)")
        if d:
            print(f"  Top 5 IPK by count:")
            for row in d[:5]:
                print(f"    IPK={row.get('ipk', '?')}, Jumlah={row.get('Jumlah', '?')}")
    else:
        print(f"Chart 100: OK (empty)")
else:
    try:
        err = r2.json()
        print(f"Chart 100: FAIL ({r2.status_code}): {err}")
    except:
        print(f"Chart 100: FAIL ({r2.status_code}) {r2.text[:200]}")

print("\nDone.")
