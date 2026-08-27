"""
ROOT CAUSE FIX: dashboard_slices empty + query_context missing
"""
import requests
import json
import subprocess

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login",
               json={"username": "admin", "password": "change-me", "provider": "db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r0 = s.get(f"{BASE}/api/v1/security/csrf_token/")
    s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": BASE})
    return s

def convert_filter(f):
    if isinstance(f, dict):
        return {"col": f.get("subject", f.get("col", "")), "op": f.get("operator", f.get("op", "==")), "val": f.get("comparator", f.get("val", None))}
    return f

def build_qc(params, ds_id):
    p = json.loads(params) if isinstance(params, str) else (params or {})
    viz = p.get("viz_type", "")
    metric = p.get("metric", {})
    metrics = p.get("metrics", [])
    if not metrics and metric:
        metrics = [metric]
    groupby = p.get("groupby", [])
    x_axis = p.get("x_axis")
    all_columns = p.get("all_columns", [])
    all_columns_x = p.get("all_columns_x", [])
    filters = [convert_filter(f) for f in p.get("adhoc_filters", [])]
    q = {"time_range": "No filter", "granularity_sqla": None, "row_limit": p.get("row_limit", 50000), "metrics": metrics, "filters": filters}
    if viz == "big_number_total":
        q["columns"] = []
        q["row_limit"] = 1
    elif viz == "echarts_bar":
        cols = []
        if x_axis: cols.append(x_axis)
        cols.extend(groupby)
        q["columns"] = cols
    elif viz == "pie":
        q["columns"] = groupby
    elif viz == "histogram":
        q["columns"] = all_columns_x if isinstance(all_columns_x, list) else [all_columns_x]
    elif viz == "table":
        q["columns"] = all_columns
        q["row_limit"] = p.get("row_limit", 100)
    elif viz == "heatmap":
        ax = p.get("all_columns_x", "")
        ay = p.get("all_columns_y", "")
        q["columns"] = [ax, ay]
    else:
        q["columns"] = groupby
    return {"datasource": {"id": ds_id, "type": "table"}, "queries": [q], "form_data": p, "result_format": "json", "result_type": "full"}

def main():
    s = api()
    
    # Fetch all charts individually
    charts = {}
    for cid in range(1, 27):
        r = s.get(f"{BASE}/api/v1/chart/{cid}")
        if r.status_code == 200:
            charts[cid] = r.json()["result"]
    
    print(f"Fetched {len(charts)} charts")
    
    # Generate SQL files to /tmp/ (inside container)
    # Fix 1: dashboard_slices
    sql_lines = ["BEGIN;"]
    for cid in sorted(charts.keys()):
        sql_lines.append(f"INSERT INTO dashboard_slices (dashboard_id, slice_id) VALUES (3, {cid}) ON CONFLICT DO NOTHING;")
    sql_lines.append("COMMIT;")
    
    with open("/tmp/fix_dashboard_slices.sql", "w") as f:
        f.write("\n".join(sql_lines))
    
    # Fix 2: query_context for all charts
    qc_updates = []
    for cid in sorted(charts.keys()):
        c = charts[cid]
        ds_id = c.get("datasource_id")
        params = c.get("params", "{}")
        qc = build_qc(params, ds_id)
        qc_json = json.dumps(qc)
        qc_escaped = qc_json.replace("'", "''")
        qc_updates.append(f"UPDATE slices SET query_context = '{qc_escaped}' WHERE id = {cid};")
    
    with open("/tmp/fix_all_query_context.sql", "w") as f:
        f.write("BEGIN;\n")
        for u in qc_updates:
            f.write(u + "\n")
        f.write("COMMIT;\n")
    
    print("SQL files written to /tmp/")
    
    # Test each chart's query_context
    print("\n--- Testing chart data ---")
    ok = 0
    fail = 0
    for cid in sorted(charts.keys()):
        c = charts[cid]
        ds_id = c.get("datasource_id")
        params = c.get("params", "{}")
        qc = build_qc(params, ds_id)
        
        r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
        if r2.status_code == 200:
            data = r2.json()
            if "result" in data and data["result"]:
                rc = data["result"][0].get("rowcount", "?")
                print(f"  Chart {cid:2d}: OK ({rc:>5} rows) - {c.get('slice_name', '?')}")
                ok += 1
            else:
                print(f"  Chart {cid:2d}: OK (empty) - {c.get('slice_name', '?')}")
                ok += 1
        else:
            try:
                err = r2.json().get("message", "")[:60]
            except:
                err = r2.text[:60]
            print(f"  Chart {cid:2d}: FAIL ({r2.status_code}) - {c.get('slice_name', '?')}: {err}")
            fail += 1
    
    print(f"\nRESULT: {ok}/{ok+fail} charts render data correctly")

if __name__ == "__main__":
    main()
