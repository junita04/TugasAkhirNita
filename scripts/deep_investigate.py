"""
Deep investigation: Test chart rendering and datasource validity.
"""

import requests
import json

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

def main():
    s = api()
    
    print("=" * 70)
    print("CHART & DATASOURCE DEEP INVESTIGATION")
    print("=" * 70)
    
    # 1. Check each chart's datasource validity
    print("\n--- CHART DATASOURCE CHECK ---")
    r = s.get(f"{BASE_URL}/api/v1/chart/?q=(page_size:100)")
    charts = r.json()["result"]
    
    ds_ids_used = set()
    for c in charts:
        cid = c["id"]
        ds_id = c.get("datasource_id")
        ds_type = c.get("datasource_type")
        ds_ids_used.add(ds_id)
        
        # Check if datasource exists
        r2 = s.get(f"{BASE_URL}/api/v1/dataset/{ds_id}")
        if r2.status_code == 200:
            ds_detail = r2.json()["result"]
            ds_name = ds_detail.get("table_name", "?")
            ds_schema = ds_detail.get("schema", "?")
            ds_cols = len(ds_detail.get("columns", []))
            print(f"  Chart {cid}: datasource={ds_id} ({ds_schema}.{ds_name}) cols={ds_cols} OK")
        else:
            print(f"  Chart {cid}: datasource={ds_id} NOT FOUND (status={r2.status_code})")
    
    # 2. Check dataset columns
    print("\n--- DATASET COLUMNS ---")
    for ds_id in sorted(ds_ids_used):
        r3 = s.get(f"{BASE_URL}/api/v1/dataset/{ds_id}")
        if r3.status_code == 200:
            ds = r3.json()["result"]
            cols = [c["column_name"] for c in ds.get("columns", [])]
            print(f"  Dataset {ds_id} ({ds.get('table_name')}): {cols}")
    
    # 3. Check if chart params reference valid columns
    print("\n--- CHART PARAMS VALIDATION ---")
    for c in charts[:5]:
        cid = c["id"]
        params = json.loads(c.get("params", "{}"))
        ds_id = c.get("datasource_id")
        
        # Get dataset columns
        r4 = s.get(f"{BASE_URL}/api/v1/dataset/{ds_id}")
        if r4.status_code == 200:
            valid_cols = {col["column_name"] for col in r4.json()["result"].get("columns", [])}
        else:
            valid_cols = set()
        
        # Check what columns the chart references
        x_axis = params.get("x_axis", "")
        metrics = params.get("metrics", [])
        groupby = params.get("groupby", [])
        all_columns = params.get("all_columns", [])
        filters = params.get("adhoc_filters", [])
        
        referenced = set()
        if x_axis: referenced.add(x_axis)
        referenced.update(groupby)
        if isinstance(all_columns, list): referenced.update(all_columns)
        for m in metrics:
            if isinstance(m, dict) and "sqlExpression" in m:
                # Parse SQL expression for column references
                sql = m["sqlExpression"]
                for col in valid_cols:
                    if col in sql:
                        referenced.add(col)
        
        invalid = referenced - valid_cols
        status = "OK" if not invalid else f"INVALID: {invalid}"
        print(f"  Chart {cid}: refs={referenced} -> {status}")
    
    # 4. Check Superset database metadata
    print("\n--- SUPERSET METADATA ---")
    # Check if we can access the metadata directly
    r5 = s.get(f"{BASE_URL}/api/v1/chart/?q=(page_size:1,columns:!(id,slice_name,params,datasource_id))")
    print(f"  Chart API available: {r5.status_code == 200}")
    
    # 5. Try to render a single chart via the explore endpoint
    print("\n--- CHART RENDER TEST ---")
    for cid in [1, 6, 13, 20]:
        r6 = s.get(f"{BASE_URL}/api/v1/chart/{cid}/data/")
        print(f"  Chart {cid} data: status={r6.status_code}")
        if r6.status_code == 200:
            try:
                data = r6.json()
                if "result" in data:
                    result = data["result"]
                    if isinstance(result, dict):
                        print(f"    keys: {list(result.keys())[:5]}")
                    elif isinstance(result, list):
                        print(f"    rows: {len(result)}")
            except:
                print(f"    (non-JSON response)")
        elif r6.status_code == 422:
            print(f"    Error: {r6.text[:200]}")
    
    # 6. Check dashboard position_json more carefully
    print("\n--- DASHBOARD POSITION ANALYSIS ---")
    r7 = s.get(f"{BASE_URL}/api/v1/dashboard/2")
    dash = r7.json()["result"]
    pos = json.loads(dash["position_json"]) if isinstance(dash["position_json"], str) else dash["position_json"]
    
    # Check for missing CHART entries
    chart_in_pos = set()
    for k, v in pos.items():
        if isinstance(v, dict) and v.get("type") == "CHART":
            meta = v.get("meta", {})
            chart_id = meta.get("chartId")
            if chart_id:
                chart_in_pos.add(chart_id)
    
    all_charts = {c["id"] for c in charts}
    missing = all_charts - chart_in_pos
    extra = chart_in_pos - all_charts
    
    print(f"  Charts in position: {sorted(chart_in_pos)}")
    print(f"  All charts: {sorted(all_charts)}")
    print(f"  Missing from position: {sorted(missing)}")
    print(f"  Extra in position: {sorted(extra)}")

if __name__ == "__main__":
    main()
