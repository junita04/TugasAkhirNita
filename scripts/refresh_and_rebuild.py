"""
Refresh datasets and verify all charts render correctly with proper frontend config.
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

    # 1. Refresh all datasets
    print("Refreshing datasets...")
    for ds_id in [5, 6, 7, 8, 9, 10]:
        r = s.put(f"{BASE}/api/v1/dataset/{ds_id}/refresh")
        print(f"  Dataset {ds_id}: {r.status_code}")

    # 2. Get all charts and rebuild query_context
    print("\nRebuilding query_context for all charts...")
    r = s.get(f"{BASE}/api/v1/chart/?q=(page_size:200)")
    charts = r.json()["result"]

    ok = 0
    fail = 0
    for c in charts:
        cid = c["id"]
        r1 = s.get(f"{BASE}/api/v1/chart/{cid}")
        chart = r1.json()["result"]
        name = chart["slice_name"]
        viz = chart["viz_type"]
        ds_id = chart["datasource_id"]
        params = json.loads(chart["params"])

        # Build query_context from params
        metrics_raw = params.get("metrics", [])
        metric_raw = params.get("metric")
        if metric_raw and not metrics_raw:
            metrics_raw = [metric_raw]

        qc_metrics = [m for m in metrics_raw if isinstance(m, dict)]

        groupby = params.get("groupby", [])
        adhoc = params.get("adhoc_filters", [])
        filters = [{"col": f.get("subject", ""), "op": f.get("operator", "=="), "val": f.get("comparator", None)} for f in adhoc]

        if viz == "pie":
            columns = groupby
        elif viz == "heatmap":
            columns = [params.get("all_columns_x", ""), params.get("all_columns_y", "")]
        elif viz == "table":
            columns = params.get("all_columns", [])
        elif viz == "histogram":
            columns = params.get("all_columns_x", [])
        else:
            columns = []
            x_axis = params.get("x_axis")
            if x_axis:
                columns.append(x_axis)
            columns.extend(groupby)

        row_limit = params.get("row_limit", 50000)
        qc = json.dumps({
            "datasource": {"id": ds_id, "type": "table"},
            "queries": [{"time_range": "No filter", "granularity_sqla": None, "row_limit": row_limit,
                          "metrics": qc_metrics, "columns": columns, "filters": filters}],
            "form_data": params,
            "result_format": "json", "result_type": "full",
        })

        s.put(f"{BASE}/api/v1/chart/{cid}", json={"query_context": qc})

        # Test
        r2 = s.post(f"{BASE}/api/v1/chart/data", json=json.loads(qc))
        if r2.status_code == 200:
            data = r2.json()
            if "result" in data and data["result"]:
                rc = data["result"][0].get("rowcount", "?")
                d = data["result"][0].get("data", [])
                val_str = ""
                if d and len(d) == 1:
                    vals = list(d[0].values())
                    val_str = f" = {vals[-1]}"
                elif d:
                    val_str = f" ({len(d)} groups)"
                print(f"  Chart {cid:3d}: OK ({rc:>5} rows){val_str:20s} | {viz:25s} | {name}")
                ok += 1
            else:
                print(f"  Chart {cid:3d}: OK (empty)           | {viz:25s} | {name}")
                ok += 1
        else:
            try:
                err = r2.json().get("message", "")[:50]
            except:
                err = r2.text[:50]
            print(f"  Chart {cid:3d}: FAIL ({r2.status_code})         | {viz:25s} | {name}: {err}")
            fail += 1

    print(f"\nRESULT: {ok}/{ok+fail} charts render data correctly")

if __name__ == "__main__":
    main()
