"""
Find which viz types work in this Superset installation.
Create test charts, set query_context, test rendering, keep only working ones.
"""
import requests
import json

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

def main():
    s = api()
    
    ds_id = 5  # data_referensi_mahasiswa
    
    viz_types = [
        "echarts_bar", "bar", "dist_bar", "bar_chart",
        "echarts_timeseries_bar", "echarts_timeseries",
        "echarts_timeseries_line", "echarts_area",
        "pie", "big_number_total", "table",
        "heatmap", "histogram", "treemap", "word_cloud",
        "box_plot", "pivot_table_v2", "line",
    ]
    
    for vt in viz_types:
        # Create chart
        chart_data = {
            "slice_name": f"TEST_{vt}",
            "viz_type": vt,
            "datasource_id": ds_id,
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": vt,
                "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"}],
                "groupby": ["angkatan"],
            }),
        }
        
        r = s.post(f"{BASE}/api/v1/chart/", json=chart_data)
        if r.status_code not in (200, 201):
            print(f"  {vt:35s}: CREATE FAILED ({r.status_code})")
            continue
        
        chart_id = r.json()["id"]
        
        # Build query_context manually
        qc = {
            "datasource": {"id": ds_id, "type": "table"},
            "queries": [{
                "time_range": "No filter",
                "row_limit": 100,
                "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"}],
                "columns": ["angkatan"],
                "filters": [],
            }],
            "form_data": {
                "viz_type": vt,
                "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "count"}],
                "groupby": ["angkatan"],
            },
            "result_format": "json",
            "result_type": "full",
        }
        
        # Save query_context to chart
        s.put(f"{BASE}/api/v1/chart/{chart_id}", json={"query_context": json.dumps(qc)})
        
        # Test render via API
        r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
        if r2.status_code == 200:
            data = r2.json()
            if "result" in data and data["result"]:
                rc = data["result"][0].get("rowcount", "?")
                print(f"  {vt:35s}: API OK ({rc} rows)")
            else:
                print(f"  {vt:35s}: API OK (empty)")
        else:
            try:
                err = r2.json().get("message", "")[:60]
            except:
                err = r2.text[:60]
            print(f"  {vt:35s}: API FAIL ({r2.status_code}): {err}")
        
        # Delete
        s.delete(f"{BASE}/api/v1/chart/{chart_id}")

if __name__ == "__main__":
    main()
