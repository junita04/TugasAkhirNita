"""
Directly update query_context in Superset metadata database
using a Python script that runs inside the postgres container.
"""

import requests
import json
import subprocess

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
    
    # Get all charts
    r = s.get(f"{BASE_URL}/api/v1/chart/?q=(page_size:100)")
    charts = r.json()["result"]
    
    # Build all updates
    updates = []
    for c in charts:
        cid = c["id"]
        ds_id = c.get("datasource_id")
        params = c.get("params", "{}")
        
        qc = build_qc(params, ds_id)
        qc_json = json.dumps(qc)
        updates.append((cid, qc_json))
    
    # Write a Python script that runs inside postgres container
    script_lines = [
        "import psycopg2",
        "import json",
        "",
        "conn = psycopg2.connect(host='localhost', database='superset', user='academic')",
        "cur = conn.cursor()",
        "",
    ]
    
    for cid, qc_json in updates:
        # Escape single quotes for SQL
        qc_escaped = qc_json.replace("'", "''")
        script_lines.append(f"cur.execute(\"UPDATE slices SET query_context = E'{qc_escaped}' WHERE id = {cid}\")")
    
    script_lines.extend([
        "conn.commit()",
        "print(f'Updated {cur.rowcount} rows')",
        "cur.close()",
        "conn.close()",
    ])
    
    script_content = "\n".join(script_lines)
    
    # Write script to temp file
    with open("/tmp/update_qc.py", "w") as f:
        f.write(script_content)
    
    # Copy to postgres container and run
    import os
    with open("D:/TA/TugasAkhirNita/scripts/update_qc_pg.py", "w") as f:
        f.write(script_content)
    
    print("Script written. Copying to postgres container...")
    
    # Use docker cp and docker exec
    os.system('docker cp D:/TA/TugasAkhirNita/scripts/update_qc_pg.py academic-datalakehouse-postgres-1:/tmp/update_qc.py')
    os.system('docker exec academic-datalakehouse-postgres-1 pip install psycopg2-binary 2>/dev/null')
    result = os.system('docker exec academic-datalakehouse-postgres-1 python /tmp/update_qc.py')
    
    print(f"Update result: {result}")
    
    # Verify
    print("\n--- Verification ---")
    import time
    time.sleep(1)
    
    for c in charts[:5]:
        cid = c["id"]
        ds_id = c.get("datasource_id")
        params = c.get("params", "{}")
        
        qc = build_qc(params, ds_id)
        r2 = s.post(f"{BASE_URL}/api/v1/chart/data", json=qc)
        
        if r2.status_code == 200:
            try:
                data = r2.json()
                if "result" in data and data["result"]:
                    rc = data["result"][0].get("rowcount", "?")
                    print(f"  Chart {cid}: OK ({rc} rows)")
                else:
                    print(f"  Chart {cid}: OK (empty)")
            except:
                print(f"  Chart {cid}: ERROR")
        else:
            print(f"  Chart {cid}: FAIL ({r2.status_code})")

if __name__ == "__main__":
    main()
