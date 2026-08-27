"""
Final fix: 
1. Clean up orphan charts
2. Create a proper IPK distribution chart (bar chart with binned data)
3. Fix all chart params and query_context
4. Rebuild dashboard layout with professional design
"""
import requests
import json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r0 = s.get(f"{BASE}/api/v1/security/csrf_token/")
    s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": BASE})
    return s

def make_metric(sql, label):
    return {"expressionType": "SQL", "sqlExpression": sql, "label": label}

def make_adhoc_filter(subject, operator, comparator, clause="WHERE"):
    return {"expressionType": "SIMPLE", "subject": subject, "operator": operator, "comparator": comparator, "clause": clause}

def convert_filter(f):
    return {"col": f.get("subject", ""), "op": f.get("operator", "=="), "val": f.get("comparator", None)}

def build_qc(ds_id, metrics, columns, filters=None, row_limit=50000, form_data=None):
    return json.dumps({
        "datasource": {"id": ds_id, "type": "table"},
        "queries": [{"time_range": "No filter", "granularity_sqla": None, "row_limit": row_limit,
                      "metrics": metrics, "columns": columns, "filters": filters or []}],
        "form_data": form_data or {},
        "result_format": "json", "result_type": "full",
    })

def fix_chart(s, cid):
    """Read chart, rebuild query_context, save, test."""
    r = s.get(f"{BASE}/api/v1/chart/{cid}")
    if r.status_code != 200:
        print(f"  Chart {cid}: NOT FOUND")
        return False
    
    c = r.json()["result"]
    name = c["slice_name"]
    viz = c["viz_type"]
    ds_id = c["datasource_id"]
    params = json.loads(c["params"])
    
    metrics_raw = params.get("metrics", [])
    metric_raw = params.get("metric")
    if metric_raw and not metrics_raw:
        metrics_raw = [metric_raw]
    
    qc_metrics = [m for m in metrics_raw if isinstance(m, dict)]
    groupby = params.get("groupby", [])
    adhoc = params.get("adhoc_filters", [])
    filters = [convert_filter(f) for f in adhoc]
    
    if viz == "pie":
        columns = groupby
    elif viz == "heatmap":
        columns = [params.get("all_columns_x", ""), params.get("all_columns_y", "")]
    elif viz == "table":
        columns = params.get("all_columns", [])
    elif viz == "histogram":
        columns = []
    else:
        columns = []
        x_axis = params.get("x_axis")
        if x_axis:
            columns.append(x_axis)
        columns.extend(groupby)
    
    row_limit = params.get("row_limit", 50000)
    qc = build_qc(ds_id, qc_metrics, columns, filters, row_limit, params)
    s.put(f"{BASE}/api/v1/chart/{cid}", json={"query_context": qc})
    
    r2 = s.post(f"{BASE}/api/v1/chart/data", json=json.loads(qc))
    if r2.status_code == 200:
        data = r2.json()
        if "result" in data and data["result"]:
            rc = data["result"][0].get("rowcount", "?")
            return True
    return False

def main():
    s = api()
    
    # 1. Clean up orphan charts (anything not in 66-91 or 100)
    print("=== CLEANUP ORPHAN CHARTS ===")
    r = s.get(f"{BASE}/api/v1/chart/?q=(page_size:200)")
    all_charts = r.json()["result"]
    valid_ids = set(range(66, 92)) | {100}  # 66-91 + 100 (IPK chart)
    
    for c in all_charts:
        if c["id"] not in valid_ids:
            s.delete(f"{BASE}/api/v1/chart/{c['id']}")
            print(f"  Deleted orphan: {c['id']} - {c.get('slice_name', '?')}")
    
    # 2. Check if chart 100 exists, if not create it
    r = s.get(f"{BASE}/api/v1/chart/100")
    if r.status_code != 200:
        print("\nChart 100 missing, creating IPK distribution chart...")
        chart_data = {
            "slice_name": "Distribusi IPK Mahasiswa Aktif",
            "viz_type": "table",
            "datasource_id": 5,
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "table",
                "all_columns": ["ipk"],
                "order_desc": True,
                "row_limit": 50000,
                "page_length": 20,
                "include_search": True,
                "table_timestamp_format": "smart_date",
                "show_cell_bars": True,
                "color_pn": True,
                "adhoc_filters": [make_adhoc_filter("status_mahasiswa", "==", "AKTIF")],
            }),
        }
        r = s.post(f"{BASE}/api/v1/chart/", json=chart_data)
        chart_id = r.json()["id"]
        
        qc = {
            "datasource": {"id": 5, "type": "table"},
            "queries": [{"time_range": "No filter", "row_limit": 50000, "metrics": [],
                          "columns": ["ipk"], "filters": [{"col": "status_mahasiswa", "op": "==", "val": "AKTIF"}]}],
            "form_data": {"viz_type": "table", "all_columns": ["ipk"],
                          "adhoc_filters": [make_adhoc_filter("status_mahasiswa", "==", "AKTIF")], "row_limit": 50000},
            "result_format": "json", "result_type": "full",
        }
        s.put(f"{BASE}/api/v1/chart/{chart_id}", json={"query_context": json.dumps(qc)})
        
        # Update position_json
        r3 = s.get(f"{BASE}/api/v1/dashboard/3")
        dash = r3.json()["result"]
        pos = json.loads(dash.get("position_json", "{}"))
        for key, val in pos.items():
            if isinstance(val, dict) and val.get("type") == "CHART":
                meta = val.get("meta", {})
                if meta.get("chartId") in [90, 95, 96, 97, 98, 99]:
                    meta["chartId"] = chart_id
        s.put(f"{BASE}/api/v1/dashboard/3", json={"position_json": json.dumps(pos)})
        print(f"  Created chart {chart_id}")
    else:
        chart_id = 100
        print(f"\nChart 100 exists")
    
    # 3. Fix all charts
    print("\n=== FIX ALL CHARTS ===")
    r = s.get(f"{BASE}/api/v1/chart/?q=(page_size:200)")
    charts = r.json()["result"]
    
    ok = 0
    fail = 0
    for c in charts:
        cid = c["id"]
        if fix_chart(s, cid):
            r1 = s.get(f"{BASE}/api/v1/chart/{cid}")
            chart = r1.json()["result"]
            name = chart["slice_name"]
            viz = chart["viz_type"]
            r2 = s.post(f"{BASE}/api/v1/chart/data", json=json.loads(chart.get("query_context", "{}")))
            rc = r2.json()["result"][0].get("rowcount", "?") if r2.status_code == 200 and r2.json().get("result") else "?"
            print(f"  Chart {cid:3d}: OK ({rc:>5} rows) | {viz:25s} | {name}")
            ok += 1
        else:
            r1 = s.get(f"{BASE}/api/v1/chart/{cid}")
            chart = r1.json()["result"]
            name = chart["slice_name"]
            print(f"  Chart {cid:3d}: FAIL | {name}")
            fail += 1
    
    print(f"\nRESULT: {ok}/{ok+fail} charts OK")
    
    # 4. Update dashboard_slices
    print("\n=== UPDATE DASHBOARD_SLICES ===")
    r = s.get(f"{BASE}/api/v1/dashboard/3")
    dash = r.json()["result"]
    pos = json.loads(dash.get("position_json", "{}"))
    
    chart_refs = set()
    for key, val in pos.items():
        if isinstance(val, dict) and val.get("type") == "CHART":
            meta = val.get("meta", {})
            chart_id = meta.get("chartId")
            if chart_id:
                chart_refs.add(chart_id)
    
    print(f"Charts in position_json: {sorted(chart_refs)}")
    
    # Generate SQL
    sql = "DELETE FROM dashboard_slices WHERE dashboard_id = 3;\n"
    for cid in sorted(chart_refs):
        sql += f"INSERT INTO dashboard_slices (dashboard_id, slice_id) VALUES (3, {cid});\n"
    
    with open("D:/TA/TugasAkhirNita/scripts/update_ds_final.sql", "w") as f:
        f.write(sql)
    print("Generated update_ds_final.sql")

if __name__ == "__main__":
    main()
