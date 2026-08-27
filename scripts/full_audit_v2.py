"""
Full audit: check all charts, registered viz types, and available color schemes
"""
import requests
import json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s

s = api()

# 1. Check all charts
print("=" * 80)
print("ALL CHARTS STATUS")
print("=" * 80)

chart_ids = [66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,91,100]
ok = 0
fail = 0
for cid in sorted(chart_ids):
    r1 = s.get(f"{BASE}/api/v1/chart/{cid}")
    if r1.status_code != 200:
        print(f"Chart {cid}: NOT FOUND")
        fail += 1
        continue
    c = r1.json()["result"]
    name = c["slice_name"]
    viz = c["viz_type"]
    qc_str = c.get("query_context")
    ds_id = c["datasource_id"]
    params = json.loads(c["params"]) if c["params"] else {}
    
    status = "NO_QC"
    rows = 0
    if qc_str:
        qc = json.loads(qc_str)
        r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
        if r2.status_code == 200:
            data = r2.json()
            if "result" in data and data["result"]:
                rows = data["result"][0].get("rowcount", 0)
                status = "OK"
            else:
                status = "EMPTY"
        else:
            try:
                err = r2.json().get("message", "")[:60]
            except:
                err = r2.text[:60]
            status = f"FAIL:{err}"
    
    marker = "OK" if status == "OK" else "!!"
    print(f"  [{marker}] Chart {cid:4d}: {viz:25s} | {status:8s} | {rows:>5} rows | ds={ds_id} | {name}")
    if status == "OK":
        ok += 1
    else:
        fail += 1

print(f"\nTotal: {ok+fail}, OK: {ok}, FAIL: {fail}")

# 2. Check dataset 5 columns for IPK
print("\n" + "=" * 80)
print("DATASET 5 (data_referensi_mahasiswa) - IPK column details")
print("=" * 80)
r = s.get(f"{BASE}/api/v1/dataset/5")
ds = r.json()["result"]
for col in ds.get("columns", []):
    if col["column_name"] == "ipk":
        print(f"  column: {col['column_name']}")
        print(f"  type: {col.get('type')}")
        print(f"  is_dttm: {col.get('is_dttm')}")
        break

# 3. Test IPK data directly via Trino
print("\n" + "=" * 80)
print("TEST IPK QUERY VIA SUPERSET SQL LAB")
print("=" * 80)

# Try creating a simple chart to test IPK distribution
# Use SQL query to get IPK bins
params_test = {
    "viz_type": "table",
    "all_columns": [],
    "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "jumlah"}],
    "groupby": ["ipk"],
    "order_desc": True,
    "row_limit": 500,
    "page_length": 20,
    "include_search": True,
    "show_cell_bars": True,
    "adhoc_filters": [{"expressionType": "SIMPLE", "subject": "status_mahasiswa", "operator": "==", "comparator": "AKTIF", "clause": "WHERE"}],
}

qc_test = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 500,
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "jumlah"}],
        "columns": ["ipk"],
        "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}],
    }],
    "form_data": params_test,
    "result_format": "json",
    "result_type": "full",
}

r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc_test)
if r2.status_code == 200:
    data = r2.json()
    rc = data["result"][0].get("rowcount", 0) if data.get("result") else 0
    print(f"IPK table test: OK ({rc} rows)")
    d = data["result"][0].get("data", []) if data.get("result") else []
    if d:
        print(f"  Sample: {d[:3]}")
else:
    print(f"IPK table test: FAIL ({r2.status_code})")
    try:
        print(f"  Error: {r2.json()}")
    except:
        print(f"  Error: {r2.text[:200]}")
