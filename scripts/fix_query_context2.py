"""
FIX QUERY CONTEXT with correct format.
Each query in query_context.queries must contain the actual
metrics/columns/filters from the chart params.
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

def build_query_context(params_str, ds_id, ds_type="table"):
    """Build correct query_context from params."""
    p = json.loads(params_str) if isinstance(params_str, str) else (params_str or {})
    
    viz_type = p.get("viz_type", "")
    
    # Build the query based on viz_type
    query = {
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": p.get("row_limit", 50000),
    }
    
    if viz_type == "big_number_total":
        metric = p.get("metric", {})
        adhoc_filters = p.get("adhoc_filters", [])
        query["metrics"] = [metric] if metric else []
        query["columns"] = []
        query["filters"] = adhoc_filters
        query["row_limit"] = 1
    
    elif viz_type == "pie":
        metrics = p.get("metrics", [])
        groupby = p.get("groupby", [])
        adhoc_filters = p.get("adhoc_filters", [])
        query["metrics"] = metrics
        query["columns"] = groupby
        query["filters"] = adhoc_filters
    
    elif viz_type == "echarts_bar":
        metrics = p.get("metrics", [])
        groupby = p.get("groupby", [])
        adhoc_filters = p.get("adhoc_filters", [])
        x_axis = p.get("x_axis")
        
        # For echarts_bar, x_axis goes into columns
        cols = []
        if x_axis:
            cols.append(x_axis)
        cols.extend(groupby)
        
        query["metrics"] = metrics
        query["columns"] = cols
        query["filters"] = adhoc_filters
    
    elif viz_type == "histogram":
        all_columns_x = p.get("all_columns_x", [])
        adhoc_filters = p.get("adhoc_filters", [])
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
        adhoc_filters = p.get("adhoc_filters", [])
        query["metrics"] = metrics
        query["columns"] = groupby
        query["filters"] = adhoc_filters
    
    qc = {
        "datasource": {"id": ds_id, "type": ds_type},
        "queries": [query],
        "form_data": p,
        "result_format": "json",
        "result_type": "full",
    }
    
    return qc

def main():
    s = api()
    
    print("=" * 70)
    print("FIXING QUERY CONTEXT (correct format)")
    print("=" * 70)
    
    r = s.get(f"{BASE_URL}/api/v1/chart/?q=(page_size:100)")
    charts = r.json()["result"]
    
    success = 0
    failed = 0
    
    for c in charts:
        cid = c["id"]
        name = c["slice_name"]
        ds_id = c.get("datasource_id")
        params = c.get("params", "{}")
        viz = c.get("viz_type", "")
        
        qc = build_query_context(params, ds_id)
        
        r2 = s.put(f"{BASE_URL}/api/v1/chart/{cid}", json={
            "query_context": json.dumps(qc),
        })
        
        if r2.status_code == 200:
            print(f"  Chart {cid:2d}: {name:45s} -> OK")
            success += 1
        else:
            print(f"  Chart {cid:2d}: {name:45s} -> FAILED ({r2.status_code})")
            failed += 1
        
        time.sleep(0.1)
    
    print(f"\nUpdated: {success} OK, {failed} FAILED")
    
    # Test rendering
    print("\n--- Testing chart data ---")
    for c in charts[:8]:
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
                    elif isinstance(result, list):
                        rc = len(result)
                    else:
                        rc = "?"
                    print(f"  Chart {cid}: OK (rows={rc})")
                else:
                    err = data.get("message", "no result key")
                    print(f"  Chart {cid}: FAILED - {str(err)[:80]}")
            except Exception as e:
                print(f"  Chart {cid}: PARSE ERROR: {e}")
        else:
            try:
                err = r3.json().get("message", r3.text[:80])
            except:
                err = r3.text[:80]
            print(f"  Chart {cid}: FAILED ({r3.status_code}): {err}")

if __name__ == "__main__":
    main()
