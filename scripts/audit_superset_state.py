"""
STEP 1: AUDIT SUPERSET STATE
=============================
Deep inspection of Superset internals to find root cause.
"""

import requests
import json

BASE_URL = "http://localhost:8088"

def api_login():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/v1/security/login",
               json={"username": "admin", "password": "change-me", "provider": "db"})
    token = r.json().get("access_token", "")
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r0 = s.get(f"{BASE_URL}/api/v1/security/csrf_token/")
    csrf = r0.json().get("result", "")
    s.headers.update({"X-CSRFToken": csrf, "Referer": BASE_URL})
    return s

def audit():
    s = api_login()
    
    print("=" * 70)
    print("SUPERSET STATE AUDIT")
    print("=" * 70)
    
    # 1. Databases
    print("\n--- DATABASES ---")
    r = s.get(f"{BASE_URL}/api/v1/database/?q=(page_size:50)")
    dbs = r.json().get("result", [])
    for db in dbs:
        print(f"  id={db['id']} name='{db['database_name']}' sqlalchemy_uri='{db.get('sqlalchemy_uri','N/A')}'")
    
    # 2. Datasets
    print("\n--- DATASETS ---")
    r = s.get(f"{BASE_URL}/api/v1/dataset/?q=(page_size:100)")
    datasets = r.json().get("result", [])
    ds_map = {}
    for ds in datasets:
        ds_id = ds["id"]
        ds_name = ds["table_name"]
        ds_schema = ds.get("schema", "")
        ds_db = ds.get("database", {})
        ds_db_id = ds.get("database_id", "N/A")
        ds_map[ds_name] = ds_id
        print(f"  id={ds_id} table='{ds_name}' schema='{ds_schema}' database_id={ds_db_id}")
    
    # 3. Charts
    print("\n--- CHARTS ---")
    r = s.get(f"{BASE_URL}/api/v1/chart/?q=(page_size:100)")
    charts = r.json().get("result", [])
    chart_ids = set()
    for c in charts:
        cid = c["id"]
        chart_ids.add(cid)
        ds_ref = c.get("datasource_id", "N/A")
        ds_type = c.get("datasource_type", "N/A")
        viz = c.get("viz_type", "N/A")
        name = c.get("slice_name", "N/A")
        params = c.get("params", None)
        params_len = len(params) if params else 0
        print(f"  id={cid} name='{name}' viz={viz} datasource_id={ds_ref} datasource_type={ds_type} params_len={params_len}")
    
    # 4. Dashboards
    print("\n--- DASHBOARDS ---")
    r = s.get(f"{BASE_URL}/api/v1/dashboard/?q=(page_size:50)")
    dashboards = r.json().get("result", [])
    for d in dashboards:
        dash_id = d["id"]
        title = d.get("dashboard_title", "N/A")
        published = d.get("published", False)
        
        # Get full dashboard detail
        r2 = s.get(f"{BASE_URL}/api/v1/dashboard/{dash_id}")
        detail = r2.json().get("result", {})
        position = detail.get("position_json", None)
        
        if position:
            if isinstance(position, str):
                pos = json.loads(position)
            else:
                pos = position
        else:
            pos = {}
        
        # Extract chart IDs from position
        pos_charts = []
        for key, val in pos.items():
            if isinstance(val, dict) and val.get("type") == "CHART":
                meta = val.get("meta", {})
                chart_id = meta.get("chartId")
                if chart_id:
                    pos_charts.append(chart_id)
        
        valid = [cid for cid in pos_charts if cid in chart_ids]
        invalid = [cid for cid in pos_charts if cid not in chart_ids]
        
        print(f"  id={dash_id} title='{title}' published={published}")
        print(f"    position_json keys: {len(pos)}")
        print(f"    chart IDs in position: {pos_charts}")
        print(f"    VALID chart IDs: {valid}")
        print(f"    INVALID chart IDs (missing): {invalid}")
        
        # Check slices association
        r3 = s.get(f"{BASE_URL}/api/v1/dashboard/{dash_id}/charts/")
        if r3.status_code == 200:
            slice_data = r3.json()
            print(f"    Dashboard slices API: {json.dumps(slice_data)[:500]}")
        else:
            print(f"    Dashboard slices API: status={r3.status_code}")
    
    # 5. Summary
    print("\n--- SUMMARY ---")
    print(f"  Databases: {len(dbs)}")
    print(f"  Datasets: {len(datasets)}")
    print(f"  Charts: {len(charts)}")
    print(f"  Dashboards: {len(dashboards)}")
    print(f"  Chart IDs: {sorted(chart_ids)}")
    
    # 6. Test query on each dataset
    print("\n--- DATASET QUERIES ---")
    for ds in datasets:
        ds_id = ds["id"]
        ds_name = ds["table_name"]
        ds_schema = ds.get("schema", "")
        
        # Get column info
        r2 = s.get(f"{BASE_URL}/api/v1/dataset/{ds_id}")
        detail = r2.json().get("result", {})
        cols = detail.get("columns", [])
        col_names = [c.get("column_name", "") for c in cols]
        
        # Try a count query
        sql = f"SELECT COUNT(*) as cnt FROM iceberg.{ds_schema}.{ds_name}"
        payload = {"database_id": 1, "sql": sql, "runAsync": False}
        r3 = s.post(f"{BASE_URL}/api/v1/sqllab/execute/", headers=s.headers, json=payload)
        try:
            qdata = r3.json()
            if "result" in qdata:
                cnt = qdata["result"].get("data", [{}])[0].get("cnt", "?")
                print(f"  {ds_schema}.{ds_name}: {cnt} rows, columns={col_names[:5]}...")
            else:
                print(f"  {ds_schema}.{ds_name}: QUERY ERROR - {json.dumps(qdata)[:200]}")
        except:
            print(f"  {ds_schema}.{ds_name}: PARSE ERROR")

if __name__ == "__main__":
    audit()
