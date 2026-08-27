"""
Fix broken charts:
1. KPIs 68-70: Filter "LULUS" -> "Lulus"
2. Pie charts 72-73: Fix ECharts pie config (label error)
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
    return {"col": f.get("subject", ""), "op": f.get("operator", "=="), "val": f.get("comparator", None)}

def build_qc(ds_id, metrics, columns, filters=None, row_limit=50000):
    return json.dumps({
        "datasource": {"id": ds_id, "type": "table"},
        "queries": [{"time_range": "No filter", "granularity_sqla": None, "row_limit": row_limit,
                      "metrics": metrics, "columns": columns, "filters": filters or []}],
        "result_format": "json", "result_type": "full",
    })

def fix_chart(s, cid, name, viz, ds_id, params):
    p = {"viz_type": viz}
    p.update(params)
    s.put(f"{BASE}/api/v1/chart/{cid}", json={"params": json.dumps(p), "viz_type": viz})

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
        columns = params.get("all_columns_x", [])
    else:
        columns = []
        x_axis = params.get("x_axis")
        if x_axis:
            columns.append(x_axis)
        columns.extend(groupby)

    row_limit = params.get("row_limit", 50000)
    qc = build_qc(ds_id, qc_metrics, columns, filters, row_limit)
    s.put(f"{BASE}/api/v1/chart/{cid}", json={"query_context": qc})

    r2 = s.post(f"{BASE}/api/v1/chart/data", json=json.loads(qc))
    if r2.status_code == 200:
        data = r2.json()
        if "result" in data and data["result"]:
            rc = data["result"][0].get("rowcount", "?")
            d = data["result"][0].get("data", [])
            print(f"  Chart {cid}: OK ({rc} rows) - {name}")
            for row in d[:3]:
                print(f"    {row}")
            return True
    try:
        err = r2.json().get("message", "")[:80]
    except:
        err = r2.text[:80]
    print(f"  Chart {cid}: FAIL ({r2.status_code}) - {name}: {err}")
    return False

def main():
    s = api()

    print("=" * 80)
    print("FIX 1: KPI CARDS - FILTER LULUS -> Lulus")
    print("=" * 80)

    flt_lulus = [make_adhoc_filter("status_mahasiswa", "==", "Lulus")]
    flt_lulus_tw = [make_adhoc_filter("status_mahasiswa", "==", "Lulus"), make_adhoc_filter("status_kelulusan", "==", "Tepat Waktu")]
    flt_lulus_tl = [make_adhoc_filter("status_mahasiswa", "==", "Lulus"), make_adhoc_filter("status_kelulusan", "==", "Terlambat")]

    # Chart 68: Mahasiswa Lulus
    fix_chart(s, 68, "Mahasiswa Lulus", "big_number_total", 5,
        {"metric": make_metric("COUNT(*)", "Mahasiswa Lulus"),
         "adhoc_filters": flt_lulus,
         "header_font_size": 0.4, "subheader_font_size": 0.15, "y_axis_format": "SMART_NUMBER"})

    # Chart 69: Tepat Waktu
    fix_chart(s, 69, "Tepat Waktu (Aktual)", "big_number_total", 5,
        {"metric": make_metric("COUNT(*)", "Tepat Waktu"),
         "adhoc_filters": flt_lulus_tw,
         "header_font_size": 0.4, "subheader_font_size": 0.15, "y_axis_format": "SMART_NUMBER"})

    # Chart 70: Terlambat
    fix_chart(s, 70, "Terlambat (Aktual)", "big_number_total", 5,
        {"metric": make_metric("COUNT(*)", "Terlambat"),
         "adhoc_filters": flt_lulus_tl,
         "header_font_size": 0.4, "subheader_font_size": 0.15, "y_axis_format": "SMART_NUMBER"})

    print("\n" + "=" * 80)
    print("FIX 2: PIE CHARTS - FIX ECHARTS LABEL CONFIG")
    print("=" * 80)

    # Chart 72: Distribusi Jenis Kelamin
    # The pie chart needs proper ECharts config. The error "Cannot read properties of undefined
    # (reading 'label')" suggests the pie chart plugin expects specific field names.
    # In Superset 6.0, the pie chart uses:
    # - metric (single metric for the pie values)
    # - groupby (for the pie slices)
    # - label_type controls what labels show
    fix_chart(s, 72, "Distribusi Jenis Kelamin", "pie", 5,
        {"metric": make_metric("COUNT(*)", "Jumlah"),
         "groupby": ["jenis_kelamin"],
         "row_limit": 10,
         "show_labels": True,
         "label_type": "key_value_percent",
         "number_format": ",d",
         "date_format": "smart_date",
         "innerRadius": 40,
         "outerRadius": 80,
         "show_legend": True,
         "labelsOutside": True})

    # Chart 73: Distribusi Status Mahasiswa
    fix_chart(s, 73, "Distribusi Status Mahasiswa", "pie", 5,
        {"metric": make_metric("COUNT(*)", "Jumlah"),
         "groupby": ["status_mahasiswa"],
         "row_limit": 10,
         "show_labels": True,
         "label_type": "key_value_percent",
         "number_format": ",d",
         "date_format": "smart_date",
         "innerRadius": 40,
         "outerRadius": 80,
         "show_legend": True,
         "labelsOutside": True})

    # Also fix other pie charts to be consistent
    print("\n" + "=" * 80)
    print("FIX 3: OTHER PIE CHARTS - SAME PATTERN")
    print("=" * 80)

    # Chart 78: Status Kelulusan Aktual
    fix_chart(s, 78, "Status Kelulusan Aktual (Tepat Waktu vs Terlambat)", "pie", 5,
        {"metric": make_metric("COUNT(*)", "Jumlah"),
         "groupby": ["status_kelulusan"],
         "row_limit": 10,
         "adhoc_filters": flt_lulus,
         "show_labels": True,
         "label_type": "key_value_percent",
         "number_format": ",d",
         "date_format": "smart_date",
         "innerRadius": 40,
         "outerRadius": 80,
         "show_legend": True,
         "labelsOutside": True})

    # Chart 88: Distribusi Prediksi ML
    fix_chart(s, 88, "Distribusi Prediksi ML (Mahasiswa Aktif)", "pie", 7,
        {"metric": make_metric("COUNT(*)", "Jumlah"),
         "groupby": ["prediksi"],
         "row_limit": 10,
         "show_labels": True,
         "label_type": "key_value_percent",
         "number_format": ",d",
         "date_format": "smart_date",
         "innerRadius": 40,
         "outerRadius": 80,
         "show_legend": True,
         "labelsOutside": True})

if __name__ == "__main__":
    main()
