"""
FIX QUERY CONTEXT v3: Correct filter format.
Superset expects filters with 'col' and 'op' not 'subject' and 'operator'.
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
    """Convert adhoc_filter to correct query_context filter format."""
    if isinstance(f, dict):
        # Superset query_context expects: col, op, val (not subject, operator, comparator)
        return {
            "col": f.get("subject", f.get("col", "")),
            "op": f.get("operator", f.get("op", "==")),
            "val": f.get("comparator", f.get("val", None)),
        }
    return f

def build_query_context(params_str, ds_id, ds_type="table"):
    p = json.loads(params_str) if isinstance(params_str, str) else (params_str or {})
    
    viz_type = p.get("viz_type", "")
    
    query = {
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": p.get("row_limit", 50000),
    }
    
    if viz_type == "big_number_total":
        metric = p.get("metric", {})
        adhoc_filters = [convert_filter(f) for f in p.get("adhoc_filters", [])]
        query["metrics"] = [metric] if metric else []
        query["columns"] = []
        query["filters"] = adhoc_filters
        query["row_limit"] = 1
    
    elif viz_type == "pie":
        metrics = p.get("metrics", [])
        groupby = p.get("groupby", [])
        adhoc_filters = [convert_filter(f) for f in p.get("adhoc_filters", [])]
        query["metrics"] = metrics
        query["columns"] = groupby
        query["filters"] = adhoc_filters
    
    elif viz_type == "echarts_bar":
        metrics = p.get("metrics", [])
        groupby = p.get("groupby", [])
        adhoc_filters = [convert_filter(f) for f in p.get("adhoc_filters", [])]
        x_axis = p.get("x_axis")
        
        cols = []
        if x_axis:
            cols.append(x_axis)
        cols.extend(groupby)
        
        query["metrics"] = metrics
        query["columns"] = cols
        query["filters"] = adhoc_filters
    
    elif viz_type == "histogram":
        all_columns_x = p.get("all_columns_x", [])
        adhoc_filters = [convert_filter(f) for f in p.get("adhoc_filters", [])]
        query["metrics"] = []
        query["columns"] = all_columns_x
        query["filters"] = adhoc_filters
    
    elif viz_type == "table":
        all_columns = p.get("all_columns", [])
        metrics = p.get("metrics", [])
        query["metrics"] = metrics
        query["columns"] = all_columns
    
    elif viz_type == "heatmap":
        all_columns_x = p.get("all_columns_x", "")
        all_columns_y = p.get("all_columns_y", "")
        metric = p.get("metric", {})
        query["metrics"] = [metric] if metric else []
        query["columns"] = [all_columns_x, all_columns_y]
    
    else:
        metrics = p.get("metrics", [])
        groupby = p.get("groupby", [])
        adhoc_filters = [convert_filter(f) for f in p.get("adhoc_filters", [])]
        query["metrics"] = metrics
        query["columns"] = groupby
        query["filters"] = adhoc_filters
    
    # Also convert filters in form_data
    form_data = dict(p)
    if "adhoc_filters" in form_data:
        form_data["adhoc_filters"] = [convert_filter(f) for f in form_data["adhoc_filters"]]
    
    qc = {
        "datasource": {"id": ds_id, "type": ds_type},
        "queries": [query],
        "form_data": form_data,
        "result_format": "json",
        "result_type": "full",
    }
    
    return qc

def main():
    s = api()
    
    print("=" * 70)
    print("FIXING QUERY CONTEXT v3 (correct filter format)")
    print("=" * 70)
    
    r = s.get(f"{BASE_URL}/api/v1/chart/?q=(page_size:100)")
    charts = r.json()["result"]
    
    success = 0
    for c in charts:
        cid = c["id"]
        name = c["slice_name"]
        ds_id = c.get("datasource_id")
        params = c.get("params", "{}")
        
        qc = build_query_context(params, ds_id)
        
        r2 = s.put(f"{BASE_URL}/api/v1/chart/{cid}", json={
            "query_context": json.dumps(qc),
        })
        
        status = "OK" if r2.status_code == 200 else f"FAIL({r2.status_code})"
        print(f"  Chart {cid:2d}: {name:45s} -> {status}")
        if r2.status_code == 200:
            success += 1
        time.sleep(0.1)
    
    print(f"\nUpdated: {success}/{len(charts)}")
    
    # Test rendering
    print("\n--- Testing chart data ---")
    for c in charts[:6]:
        cid = c["id"]
        name = c["slice_name"]
        r3 = s.get(f"{BASE_URL}/api/v1/chart/{cid}/data/")
        if r3.status_code == 200:
            try:
                data = r3.json()
                if "result" in data:
                    result = data["result"]
                    if isinstance(result, dict):
                        rc = result.get("rowcount", "?")
                    else:
                        rc = len(result) if isinstance(result, list) else "?"
                    print(f"  Chart {cid}: OK (rows={rc})")
                else:
                    print(f"  Chart {cid}: FAILED - {data.get('message', 'unknown')}")
            except Exception as e:
                print(f"  Chart {cid}: ERROR: {e}")
        else:
            try:
                err = r3.json()
                msg = err.get("message", err.get("errors", [{}])[0].get("message", r3.text[:80]))
            except:
                msg = r3.text[:80]
            print(f"  Chart {cid}: FAILED ({r3.status_code}): {msg}")

if __name__ == "__main__":
    main()
