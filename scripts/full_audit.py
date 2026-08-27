"""
Comprehensive audit of all charts + check registered viz types + dataset schemas
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

# 1. Dashboard layout
print("=" * 80)
print("DASHBOARD LAYOUT")
print("=" * 80)
r = s.get(f"{BASE}/api/v1/dashboard/3")
dash = r.json()["result"]
pos = json.loads(dash.get("position_json", "{}"))

chart_refs = []
for key, val in pos.items():
    if isinstance(val, dict) and val.get("type") == "CHART":
        meta = val.get("meta", {})
        chart_id = meta.get("chartId")
        height = meta.get("height", "?")
        width = meta.get("width", "?")
        if chart_id:
            chart_refs.append((chart_id, height, width))
            print(f"  Chart {chart_id}: {height}h x {width}w")

print(f"\nTotal charts in layout: {len(chart_refs)}")

# 2. All charts detail
print("\n" + "=" * 80)
print("ALL CHARTS DETAIL")
print("=" * 80)

for cid, h, w in sorted(chart_refs, key=lambda x: x[0]):
    r1 = s.get(f"{BASE}/api/v1/chart/{cid}")
    if r1.status_code != 200:
        print(f"Chart {cid}: NOT FOUND")
        continue
    c = r1.json()["result"]
    name = c["slice_name"]
    viz = c["viz_type"]
    ds_id = c["datasource_id"]
    params = json.loads(c["params"]) if c["params"] else {}
    qc_str = c.get("query_context")
    
    # Test query
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
                err = r2.json().get("message", "")[:50]
            except:
                err = r2.text[:50]
            status = f"FAIL: {err}"
    
    print(f"\nChart {cid:4d}: {viz:25s} | {status:8s} | {rows:>5} rows | {name}")
    print(f"  ds_id={ds_id}, layout_h={h}, layout_w={w}")
    
    # Show key params
    if viz == "table":
        all_cols = params.get("all_columns", [])
        metrics = params.get("metrics", [])
        groupby = params.get("groupby", [])
        adhoc = params.get("adhoc_filters", [])
        print(f"  all_columns={all_cols}, metrics={metrics}, groupby={groupby}")
        if adhoc:
            print(f"  filters={adhoc}")
    elif viz == "pie":
        metric = params.get("metric", {})
        groupby = params.get("groupby", [])
        adhoc = params.get("adhoc_filters", [])
        print(f"  metric={metric.get('label','?')}, groupby={groupby}")
        if adhoc:
            print(f"  filters={adhoc}")
    elif viz == "big_number_total":
        metric = params.get("metric", {})
        adhoc = params.get("adhoc_filters", [])
        print(f"  metric={metric.get('label','?')}")
        if adhoc:
            print(f"  filters={adhoc}")
    elif "echarts" in viz:
        metrics = params.get("metrics", [])
        groupby = params.get("groupby", [])
        x_axis = params.get("x_axis", "?")
        adhoc = params.get("adhoc_filters", [])
        print(f"  x_axis={x_axis}, metrics={[m.get('label','?') if isinstance(m,dict) else m for m in metrics]}, groupby={groupby}")
        if adhoc:
            print(f"  filters={adhoc}")

# 3. Dataset schemas
print("\n" + "=" * 80)
print("DATASET SCHEMAS")
print("=" * 80)

for ds_id in [5, 6, 7, 8, 9, 10]:
    r = s.get(f"{BASE}/api/v1/dataset/{ds_id}")
    if r.status_code == 200:
        ds = r.json()["result"]
        cols = [(c["column_name"], c.get("type", "?")) for c in ds.get("columns", [])]
        print(f"\nDataset {ds_id}: {ds['table_name']}")
        for cn, ct in cols:
            print(f"  {cn}: {ct}")
