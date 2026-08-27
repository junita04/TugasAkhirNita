"""
FIX: Add query_context to all charts.
Charts created via API only have params but not query_context.
We need to generate proper query_context for each chart.
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

def make_query_context(params, ds_id, ds_type="table"):
    """Build a query_context from chart params."""
    params_obj = json.loads(params) if isinstance(params, str) else params
    
    # Build the query object based on viz_type
    viz_type = params_obj.get("viz_type", "")
    
    # Build form_data
    form_data = dict(params_obj)
    
    # Build queries
    queries = []
    
    if viz_type == "big_number_total":
        # Simple metric query
        metrics = [params_obj.get("metric", {})]
        adhoc_filters = params_obj.get("adhoc_filters", [])
        query = {
            "metrics": metrics,
            "filters": adhoc_filters,
            "row_limit": 1,
            "time_range": "No filter",
        }
        queries.append(query)
    
    elif viz_type in ("echarts_bar", "pie", "histogram"):
        metrics = params_obj.get("metrics", [])
        groupby = params_obj.get("groupby", [])
        adhoc_filters = params_obj.get("adhoc_filters", [])
        x_axis = params_obj.get("x_axis")
        
        query = {
            "metrics": metrics,
            "columns": groupby if groupby else ([x_axis] if x_axis else []),
            "filters": adhoc_filters,
            "row_limit": params_obj.get("row_limit", 50000),
            "time_range": "No filter",
        }
        if x_axis and x_axis not in groupby:
            query["columns"] = [x_axis] + groupby
        queries.append(query)
    
    elif viz_type == "table":
        all_columns = params_obj.get("all_columns", [])
        metrics = params_obj.get("metrics", [])
        query = {
            "metrics": metrics,
            "columns": all_columns,
            "row_limit": params_obj.get("row_limit", 100),
            "time_range": "No filter",
        }
        queries.append(query)
    
    elif viz_type == "heatmap":
        all_columns_x = params_obj.get("all_columns_x", "")
        all_columns_y = params_obj.get("all_columns_y", "")
        metric = params_obj.get("metric", {})
        query = {
            "metrics": [metric],
            "columns": [all_columns_x, all_columns_y],
            "row_limit": 50000,
            "time_range": "No filter",
        }
        queries.append(query)
    
    else:
        # Generic fallback
        metrics = params_obj.get("metrics", [])
        groupby = params_obj.get("groupby", [])
        adhoc_filters = params_obj.get("adhoc_filters", [])
        query = {
            "metrics": metrics,
            "columns": groupby,
            "filters": adhoc_filters,
            "row_limit": params_obj.get("row_limit", 50000),
            "time_range": "No filter",
        }
        queries.append(query)
    
    query_context = {
        "datasource": {"id": ds_id, "type": ds_type},
        "queries": queries,
        "form_data": form_data,
        "result_format": "json",
        "result_type": "full",
    }
    
    return query_context

def main():
    s = api()
    
    print("=" * 70)
    print("ADDING QUERY_CONTEXT TO CHARTS")
    print("=" * 70)
    
    # Get all charts
    r = s.get(f"{BASE_URL}/api/v1/chart/?q=(page_size:100)")
    charts = r.json()["result"]
    
    success = 0
    failed = 0
    
    for c in charts:
        cid = c["id"]
        name = c["slice_name"]
        ds_id = c.get("datasource_id")
        params = c.get("params", "{}")
        
        # Generate query_context
        qc = make_query_context(params, ds_id)
        
        # Update chart with query_context
        r2 = s.put(f"{BASE_URL}/api/v1/chart/{cid}", json={
            "query_context": json.dumps(qc),
        })
        
        if r2.status_code == 200:
            print(f"  Chart {cid:2d}: {name:45s} -> OK")
            success += 1
        else:
            print(f"  Chart {cid:2d}: {name:45s} -> FAILED ({r2.status_code}): {r2.text[:100]}")
            failed += 1
        
        time.sleep(0.2)
    
    print(f"\nUpdated: {success} OK, {failed} FAILED")
    
    # Test chart rendering again
    print("\n--- Testing chart rendering ---")
    test_count = 0
    ok_count = 0
    for c in charts[:10]:
        cid = c["id"]
        r3 = s.get(f"{BASE_URL}/api/v1/chart/{cid}/data/")
        if r3.status_code == 200:
            try:
                data = r3.json()
                if "result" in data:
                    result = data["result"]
                    rowcount = result.get("rowcount", 0) if isinstance(result, dict) else len(result)
                    print(f"  Chart {cid}: OK (rows={rowcount})")
                    ok_count += 1
                else:
                    print(f"  Chart {cid}: NO RESULT")
            except:
                print(f"  Chart {cid}: PARSE ERROR")
        else:
            try:
                err = r3.json()
                msg = err.get("message", "")[:80]
            except:
                msg = r3.text[:80]
            print(f"  Chart {cid}: FAILED ({r3.status_code}): {msg}")
        test_count += 1
    
    print(f"\nRender test: {ok_count}/{test_count} OK")

if __name__ == "__main__":
    main()
