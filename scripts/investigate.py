"""
INVESTIGASI LENGKAP: Data scope, metrics, dan chart redundancy
"""
import requests, json, os

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login", json={"username":"admin","password":"change-me","provider":"db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s

s = api()

# ============================================================
# 1. INVESTIGASI DATA SCOPE
# ============================================================
print("=" * 80)
print("1. INVESTIGASI DATA SCOPE")
print("=" * 80)

# Check total data in gold table
print("\n--- Gold Table: data_referensi_mahasiswa ---")
r = s.get(f"{BASE}/api/v1/chart/66")  # Total Mahasiswa
c = r.json()["result"]
qc = json.loads(c["query_context"])
r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
if r2.status_code == 200:
    data = r2.json()
    d = data["result"][0].get("data", [])
    print(f"Total Mahasiswa (no filter): {d}")

# Check with status filter
r = s.get(f"{BASE}/api/v1/chart/67")  # Aktif
c = r.json()["result"]
qc = json.loads(c["query_context"])
r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
if r2.status_code == 200:
    data = r2.json()
    d = data["result"][0].get("data", [])
    print(f"Mahasiswa Aktif: {d}")

r = s.get(f"{BASE}/api/v1/chart/68")  # Lulus
c = r.json()["result"]
qc = json.loads(c["query_context"])
r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
if r2.status_code == 200:
    data = r2.json()
    d = data["result"][0].get("data", [])
    print(f"Mahasiswa Lulus: {d}")

# Check dataset 5 directly for scope analysis
print("\n--- Direct query: dataset 5 scope ---")
# Query: count by status_mahasiswa
qc_scope = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 100,
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "jumlah"}],
        "columns": ["status_mahasiswa"],
    }],
    "form_data": {},
    "result_format": "json",
    "result_type": "full",
}
r = s.post(f"{BASE}/api/v1/chart/data", json=qc_scope)
if r.status_code == 200:
    data = r.json()
    d = data["result"][0].get("data", [])
    print(f"Count by status_mahasiswa:")
    total = 0
    for row in d:
        print(f"  {row}")
        total += row.get("jumlah", 0)
    print(f"  TOTAL: {total}")

# Check semester distribution
print("\n--- Semester distribution ---")
qc_sem = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 100,
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "jumlah"}],
        "columns": ["semester"],
    }],
    "form_data": {},
    "result_format": "json",
    "result_type": "full",
}
r = s.post(f"{BASE}/api/v1/chart/data", json=qc_sem)
if r.status_code == 200:
    data = r.json()
    d = data["result"][0].get("data", [])
    print(f"Count by semester:")
    for row in sorted(d, key=lambda x: x.get("semester", 0)):
        print(f"  semester {row.get('semester')}: {row.get('jumlah')}")

# Check: Aktif + Lulus only, semester >= 5
print("\n--- Scope: Aktif + Lulus, semester >= 5 ---")
qc_research = {
    "datasource": {"id": 5, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 100,
        "metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "jumlah"}],
        "columns": ["status_mahasiswa"],
        "filters": [
            {"col": "semester", "op": ">=", "val": 5},
        ],
    }],
    "form_data": {},
    "result_format": "json",
    "result_type": "full",
}
r = s.post(f"{BASE}/api/v1/chart/data", json=qc_research)
if r.status_code == 200:
    data = r.json()
    d = data["result"][0].get("data", [])
    print(f"Aktif + Lulus, semester >= 5:")
    total = 0
    for row in d:
        if row.get("status_mahasiswa") in ["AKTIF", "Lulus"]:
            print(f"  {row}")
            total += row.get("jumlah", 0)
    print(f"  TOTAL (Aktif+Lulus, sem>=5): {total}")

# ============================================================
# 2. INVESTIGASI ML METRICS
# ============================================================
print("\n" + "=" * 80)
print("2. INVESTIGASI ML METRICS")
print("=" * 80)

# Check model_metrics table
print("\n--- model_metrics (dataset 6) ---")
qc_metrics = {
    "datasource": {"id": 6, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [],
        "columns": ["model", "cv_mean_accuracy", "cv_mean_f1", "test_accuracy", "test_precision", "test_recall", "test_f1", "training_samples", "test_samples", "inference_samples", "pipeline_version", "training_date"],
    }],
    "form_data": {},
    "result_format": "json",
    "result_type": "full",
}
r = s.post(f"{BASE}/api/v1/chart/data", json=qc_metrics)
if r.status_code == 200:
    data = r.json()
    d = data["result"][0].get("data", [])
    for row in d:
        print(f"  {row}")

# Check classification_report
print("\n--- classification_report (dataset 10) ---")
qc_cr = {
    "datasource": {"id": 10, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [],
        "columns": ["class", "precision", "recall", "f1_score", "support"],
    }],
    "form_data": {},
    "result_format": "json",
    "result_type": "full",
}
r = s.post(f"{BASE}/api/v1/chart/data", json=qc_cr)
if r.status_code == 200:
    data = r.json()
    d = data["result"][0].get("data", [])
    for row in d:
        print(f"  {row}")

# Check confusion_matrix
print("\n--- confusion_matrix (dataset 9) ---")
qc_cm = {
    "datasource": {"id": 9, "type": "table"},
    "queries": [{
        "time_range": "No filter",
        "granularity_sqla": None,
        "row_limit": 10,
        "metrics": [],
        "columns": ["actual", "predicted", "count"],
    }],
    "form_data": {},
    "result_format": "json",
    "result_type": "full",
}
r = s.post(f"{BASE}/api/v1/chart/data", json=qc_cm)
if r.status_code == 200:
    data = r.json()
    d = data["result"][0].get("data", [])
    for row in d:
        print(f"  {row}")

# Check model files on disk
print("\n--- Model files on disk ---")
model_dir = "D:/TA/TugasAkhirNita/results"
if os.path.exists(model_dir):
    for f in os.listdir(model_dir):
        fpath = os.path.join(model_dir, f)
        if os.path.isfile(fpath):
            size = os.path.getsize(fpath)
            print(f"  {f} ({size} bytes)")
else:
    print(f"  Directory not found: {model_dir}")

# Check for model JSON files
results_dir = "D:/TA/TugasAkhirNita/results"
for f in ["metrics.json", "classification_report.json", "confusion_matrix.json"]:
    fpath = os.path.join(results_dir, f)
    if os.path.exists(fpath):
        with open(fpath) as fh:
            content = json.load(fh)
        print(f"\n  {f}:")
        print(f"  {json.dumps(content, indent=2)[:500]}")
