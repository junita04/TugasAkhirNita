"""
STEP 1: AUDIT DASHBOARD - Read position_json, check chart IDs, validate definitions
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

    print("=" * 90)
    print("STEP 1: AUDIT DASHBOARD ID 3")
    print("=" * 90)

    # 1. Read dashboard
    r = s.get(f"{BASE}/api/v1/dashboard/3")
    if r.status_code != 200:
        print(f"DASHBOARD NOT FOUND: {r.status_code}")
        return
    dash = r.json()["result"]
    print(f"Dashboard ID: {dash['id']}")
    print(f"Title: {dash['dashboard_title']}")
    print(f"Published: {dash['published']}")
    print(f"Slug: {dash.get('slug', 'N/A')}")

    # 2. Parse position_json
    pos_str = dash.get("position_json", "{}")
    pos = json.loads(pos_str) if pos_str else {}

    # Extract chart references from position_json
    chart_refs = []
    for key, val in pos.items():
        if isinstance(val, dict):
            # Check for chart type
            if val.get("type") == "CHART":
                meta = val.get("meta", {})
                chart_id = meta.get("chartId")
                if chart_id:
                    chart_refs.append({
                        "key": key,
                        "chartId": chart_id,
                        "sliceName": meta.get("sliceName", ""),
                        "width": meta.get("width"),
                        "height": meta.get("height"),
                    })

    print(f"\nCharts in position_json: {len(chart_refs)}")

    # 3. Get ALL charts from Superset
    r2 = s.get(f"{BASE}/api/v1/chart/?q=(page_size:200)")
    all_charts = {c["id"]: c for c in r2.json()["result"]}
    print(f"Total charts in Superset: {len(all_charts)}")

    # 4. Cross-reference
    print(f"\n{'='*90}")
    print(f"{'REF':>4} | {'EXISTS':>6} | {'CHART_ID':>8} | {'CHART_NAME':<40} | {'DATASOURCE':>10} | {'VIZ_TYPE':<20} | {'QC_LEN':>6} | {'STATUS'}")
    print(f"{'-'*90}")

    valid = 0
    broken = 0
    for i, ref in enumerate(chart_refs, 1):
        cid = ref["chartId"]
        exists = cid in all_charts
        if exists:
            c = all_charts[cid]
            name = c.get("slice_name", "?")
            ds_id = c.get("datasource_id")
            ds_type = c.get("datasource_type")
            viz = c.get("viz_type", "?")
            qc = c.get("query_context", "")
            qc_len = len(qc) if qc else 0
            params = c.get("params", "")
            params_len = len(params) if params else 0

            status = "OK" if qc_len > 0 and ds_id else "WARN"
            if qc_len == 0:
                status = "NO_QC"
            if not ds_id:
                status = "NO_DS"

            print(f"{i:4d} | {'YES':>6} | {cid:8d} | {name:<40} | {ds_id:>10} | {viz:<20} | {qc_len:>6} | {status}")
            valid += 1
        else:
            print(f"{i:4d} | {'NO':>6} | {cid:8d} | {'--- MISSING ---':<40} | {'---':>10} | {'---':<20} | {'---':>6} | BROKEN")
            broken += 1

    print(f"{'='*90}")
    print(f"VALID: {valid} | BROKEN: {broken} | TOTAL REFS: {len(chart_refs)}")

    # 5. Check for orphan charts (exist but not in any dashboard)
    print(f"\n--- ORPHAN CHARTS (not in dashboard 3) ---")
    ref_ids = {r["chartId"] for r in chart_refs}
    for cid, c in sorted(all_charts.items()):
        if cid not in ref_ids:
            print(f"  Chart {cid}: {c.get('slice_name', '?')} (viz={c.get('viz_type')}, ds={c.get('datasource_id')})")

    # 6. Print chart definitions for debugging
    print(f"\n--- CHART DEFINITIONS ---")
    for ref in chart_refs:
        cid = ref["chartId"]
        if cid in all_charts:
            c = all_charts[cid]
            qc = c.get("query_context", "")
            params = c.get("params", "")
            print(f"\nChart {cid} ({c.get('slice_name')}):")
            print(f"  viz_type: {c.get('viz_type')}")
            print(f"  datasource_id: {c.get('datasource_id')}")
            print(f"  datasource_type: {c.get('datasource_type')}")
            print(f"  params: {params[:200]}...")
            if qc:
                qc_obj = json.loads(qc)
                queries = qc_obj.get("queries", [])
                if queries:
                    q0 = queries[0]
                    print(f"  QC metrics: {q0.get('metrics', [])}")
                    print(f"  QC columns: {q0.get('columns', [])}")
                    print(f"  QC filters: {q0.get('filters', [])}")
                    print(f"  QC row_limit: {q0.get('row_limit')}")
                else:
                    print(f"  QC queries: EMPTY")
            else:
                print(f"  query_context: NONE")

if __name__ == "__main__":
    main()
