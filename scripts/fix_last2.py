"""
FIX LAST 2 CHARTS: table and histogram types need special handling.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/v1/security/login",
               json={"username": "admin", "password": "change-me", "provider": "db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r0 = s.get(f"{BASE_URL}/api/v1/security/csrf_token/")
    s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": BASE_URL})
    return s

def convert_filter(f):
    if isinstance(f, dict):
        return {
            "col": f.get("subject", f.get("col", "")),
            "op": f.get("operator", f.get("op", "==")),
            "val": f.get("comparator", f.get("val", None)),
        }
    return f

def build_qc(params_str, ds_id):
    p = json.loads(params_str) if isinstance(params_str, str) else (params_str or {})
    viz = p.get("viz_type", "")
    
    metric = p.get("metric", {})
    metrics = p.get("metrics", [])
    if not metrics and metric:
        metrics = [metric]
    
    groupby = p.get("groupby", [])
    x_axis = p.get("x_axis")
    all_columns = p.get("all_columns", [])
    all_columns_x = p.get("all_columns_x", [])
    adhoc_filters = [convert_filter(f) for f in p.get("adhoc_filters", [])]
    
    query = {
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": p.get("row_limit", 50000),
        "metrics": metrics,
        "filters": adhoc_filters,
    }
    
    if viz == "big_number_total":
        query["columns"] = []
        query["row_limit"] = 1
    elif viz == "echarts_bar":
        cols = []
        if x_axis:
            cols.append(x_axis)
        cols.extend(groupby)
        query["columns"] = cols
    elif viz == "pie":
        query["columns"] = groupby
    elif viz == "histogram":
        query["columns"] = all_columns_x if isinstance(all_columns_x, list) else [all_columns_x]
    elif viz == "table":
        query["columns"] = all_columns
        query["row_limit"] = p.get("row_limit", 100)
    elif viz == "heatmap":
        ax = p.get("all_columns_x", "")
        ay = p.get("all_columns_y", "")
        query["columns"] = [ax, ay]
    else:
        query["columns"] = groupby
    
    return {
        "datasource": {"id": ds_id, "type": "table"},
        "queries": [query],
        "form_data": p,
        "result_format": "json",
        "result_type": "full",
    }

def main():
    s = api()
    
    # Fix charts 21 and 25 specifically
    for cid in [21, 25]:
        r = s.get(f"{BASE_URL}/api/v1/chart/{cid}")
        c = r.json()["result"]
        name = c["slice_name"]
        ds_id = c["datasource_id"]
        params = c["params"]
        
        qc = build_qc(params, ds_id)
        
        # Update chart
        r2 = s.put(f"{BASE_URL}/api/v1/chart/{cid}", json={"query_context": json.dumps(qc)})
        print(f"Chart {cid} ({name}): update={r2.status_code}")
        
        # Test
        r3 = s.post(f"{BASE_URL}/api/v1/chart/data", json=qc)
        if r3.status_code == 200:
            data = r3.json()
            if "result" in data and data["result"]:
                rc = data["result"][0].get("rowcount", "?")
                print(f"  Render: OK (rows={rc})")
        else:
            print(f"  Render: FAILED ({r3.status_code})")
    
    # Final test of ALL charts
    print("\n--- FINAL TEST ALL CHARTS ---")
    r = s.get(f"{BASE_URL}/api/v1/chart/?q=(page_size:100)")
    charts = r.json()["result"]
    
    ok = 0
    fail = 0
    for c in charts:
        cid = c["id"]
        name = c["slice_name"]
        ds_id = c.get("datasource_id")
        params = c.get("params", "{}")
        
        qc = build_qc(params, ds_id)
        r2 = s.post(f"{BASE_URL}/api/v1/chart/data", json=qc)
        
        if r2.status_code == 200:
            try:
                data = r2.json()
                if "result" in data and data["result"]:
                    rc = data["result"][0].get("rowcount", "?")
                    print(f"  Chart {cid:2d}: OK ({rc} rows) - {name}")
                    ok += 1
                else:
                    print(f"  Chart {cid:2d}: OK (empty) - {name}")
                    ok += 1
            except:
                print(f"  Chart {cid:2d}: ERROR - {name}")
                fail += 1
        else:
            try:
                err = r2.json().get("message", "")[:60]
            except:
                err = r2.text[:60]
            print(f"  Chart {cid:2d}: FAIL ({r2.status_code}) - {name}: {err}")
            fail += 1
    
    print(f"\nRESULT: {ok}/{len(charts)} charts working")

if __name__ == "__main__":
    main()
