"""
Fix the remaining failing charts:
- Charts 74-80: Filter LULUS -> Lulus
- Chart 85: heatmap metric fix
- Chart 87: prediction_by_angkatan metric fix
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

def make_metric(sql, label):
    return {"expressionType": "SQL", "sqlExpression": sql, "label": label}

def make_adhoc_filter(subject, operator, comparator, clause="WHERE"):
    return {"expressionType": "SIMPLE", "subject": subject, "operator": operator, "comparator": comparator, "clause": clause}

def convert_filter(f):
    if isinstance(f, dict):
        return {"col": f.get("subject", ""), "op": f.get("operator", "=="), "val": f.get("comparator", None)}
    return f

def build_qc(ds_id, metrics, columns, filters=None, row_limit=50000):
    return json.dumps({
        "datasource": {"id": ds_id, "type": "table"},
        "queries": [{"time_range": "No filter", "granularity_sqla": None, "row_limit": row_limit,
                      "metrics": metrics, "columns": columns, "filters": filters or []}],
        "result_format": "json", "result_type": "full",
    })

def update_and_test(s, cid, name, viz, ds_id, params):
    # Update params
    p = {"viz_type": viz}
    p.update(params)
    s.put(f"{BASE}/api/v1/chart/{cid}", json={"params": json.dumps(p), "viz_type": viz})
    
    # Build and set query_context
    metrics_raw = params.get("metrics", [])
    metric_raw = params.get("metric")
    if metric_raw and not metrics_raw:
        metrics_raw = [metric_raw]
    
    qc_metrics = []
    for m in metrics_raw:
        if isinstance(m, dict):
            qc_metrics.append(m)
    
    groupby = params.get("groupby", [])
    x_axis = params.get("x_axis")
    adhoc_filters = params.get("adhoc_filters", [])
    filters = [convert_filter(f) for f in adhoc_filters]
    
    if viz == "heatmap":
        columns = [params.get("all_columns_x", ""), params.get("all_columns_y", "")]
    elif viz == "pie":
        columns = groupby
    elif viz == "table":
        columns = params.get("all_columns", [])
    else:
        columns = []
        if x_axis:
            columns.append(x_axis)
        columns.extend(groupby)
    
    row_limit = params.get("row_limit", 50000)
    qc = build_qc(ds_id, qc_metrics, columns, filters, row_limit)
    s.put(f"{BASE}/api/v1/chart/{cid}", json={"query_context": qc})
    
    # Test
    r2 = s.post(f"{BASE}/api/v1/chart/data", json=json.loads(qc))
    if r2.status_code == 200:
        data = r2.json()
        if "result" in data and data["result"]:
            rc = data["result"][0].get("rowcount", "?")
            print(f"  Chart {cid}: OK ({rc} rows) - {name}")
            return True
        else:
            print(f"  Chart {cid}: OK (empty) - {name}")
            return True
    else:
        try:
            err = r2.json().get("message", "")[:80]
        except:
            err = r2.text[:80]
        print(f"  Chart {cid}: FAIL ({r2.status_code}) - {name}: {err}")
        return False

def main():
    s = api()
    
    flt_lulus = [make_adhoc_filter("status_mahasiswa", "==", "Lulus")]
    
    print("=" * 80)
    print("FIXING CHARTS 74-80 (LULUS -> Lulus)")
    print("=" * 80)
    
    ok = 0
    fail = 0
    
    fixes = [
        (74, "Rata-rata IPK per Angkatan (Lulus)", "echarts_timeseries_bar", 5,
         {"x_axis": "angkatan", "metrics": [make_metric("ROUND(AVG(ipk), 2)", "Rata-rata IPK")],
          "groupby": [], "row_limit": 50, "adhoc_filters": flt_lulus,
          "truncate_metric": True, "show_legend": False, "stack": False, "orientation": "vertical"}),
        
        (75, "Rata-rata Total SKS per Angkatan (Lulus)", "echarts_timeseries_bar", 5,
         {"x_axis": "angkatan", "metrics": [make_metric("ROUND(AVG(total_sks), 1)", "Rata-rata Total SKS")],
          "groupby": [], "row_limit": 50, "adhoc_filters": flt_lulus,
          "truncate_metric": True, "show_legend": False, "stack": False, "orientation": "vertical"}),
        
        (76, "Rata-rata Selisih SKS per Angkatan (Lulus)", "echarts_timeseries_bar", 5,
         {"x_axis": "angkatan", "metrics": [make_metric("ROUND(AVG(selisih_sks), 1)", "Rata-rata Selisih SKS")],
          "groupby": [], "row_limit": 50, "adhoc_filters": flt_lulus,
          "truncate_metric": True, "show_legend": False, "stack": False, "orientation": "vertical"}),
        
        (77, "Rata-rata Lama Studi per Angkatan (Lulus)", "echarts_timeseries_bar", 5,
         {"x_axis": "angkatan", "metrics": [make_metric("ROUND(AVG(lama_studi), 2)", "Rata-rata Lama Studi")],
          "groupby": [], "row_limit": 50, "adhoc_filters": flt_lulus,
          "truncate_metric": True, "show_legend": False, "stack": False, "orientation": "vertical"}),
        
        (78, "Status Kelulusan Aktual (Tepat Waktu vs Terlambat)", "pie", 5,
         {"metrics": [make_metric("COUNT(*)", "Jumlah")], "groupby": ["status_kelulusan"],
          "row_limit": 10, "adhoc_filters": flt_lulus, "show_labels": True,
          "label_type": "key_value_percent", "number_format": ",d", "innerRadius": 40, "outerRadius": 80}),
        
        (79, "Status Kelulusan per Angkatan (Stacked)", "echarts_timeseries_bar", 5,
         {"x_axis": "angkatan", "metrics": [make_metric("COUNT(*)", "Jumlah")],
          "groupby": ["status_kelulusan"], "row_limit": 50, "adhoc_filters": flt_lulus,
          "stack": True, "show_legend": True, "orientation": "vertical"}),
        
        (80, "Persentase Tepat Waktu per Angkatan", "echarts_timeseries_bar", 5,
         {"x_axis": "angkatan",
          "metrics": [make_metric("ROUND(COUNT(CASE WHEN status_kelulusan='Tepat Waktu' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2)", "Persentase TW (%)")],
          "groupby": [], "row_limit": 50, "adhoc_filters": flt_lulus,
          "truncate_metric": True, "show_legend": False, "stack": False, "orientation": "vertical"}),
    ]
    
    for cid, name, viz, ds_id, params in fixes:
        if update_and_test(s, cid, name, viz, ds_id, params):
            ok += 1
        else:
            fail += 1
    
    print(f"\nCharts 74-80: {ok} OK, {fail} FAIL")
    
    # Fix chart 85 (Confusion Matrix)
    print("\n" + "=" * 80)
    print("FIXING CHART 85 (Confusion Matrix)")
    print("=" * 80)
    
    # The confusion_matrix table has columns: actual, predicted, count
    # For heatmap, we need a proper aggregate metric
    update_and_test(s, 85, "Confusion Matrix", "heatmap", 9,
        {"all_columns_x": "actual", "all_columns_y": "predicted",
         "metric": make_metric("SUM(count)", "Jumlah"),
         "linear_color_scheme": "superset_seq_1", "show_legend": True,
         "show_values": True, "normalize_across": "heatmap"})
    
    # Fix chart 87 (Prediksi ML per Angkatan)
    print("\n" + "=" * 80)
    print("FIXING CHART 87 (Prediksi ML per Angkatan)")
    print("=" * 80)
    
    # prediction_by_angkatan has pre-aggregated values: prediksi_tepat_waktu, prediksi_terlambat
    # Use MAX() since values are already aggregated per angkatan
    update_and_test(s, 87, "Prediksi ML per Angkatan (Aktif)", "echarts_timeseries_bar", 8,
        {"x_axis": "angkatan",
         "metrics": [make_metric("MAX(prediksi_tepat_waktu)", "Prediksi Tepat Waktu"),
                     make_metric("MAX(prediksi_terlambat)", "Prediksi Terlambat")],
         "groupby": [], "row_limit": 50, "stack": True, "show_legend": True, "orientation": "vertical"})

if __name__ == "__main__":
    main()
