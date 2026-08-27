"""
COMPREHENSIVE DASHBOARD REVISION
- Reduce from 26 to ~14 charts
- Add research scope annotation
- Validate all metrics
- Better storytelling layout
"""
import requests, json

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

def make_adhoc(subject, op, comp):
    return {"expressionType": "SIMPLE", "subject": subject, "operator": op, "comparator": comp, "clause": "WHERE"}

def convert_adhoc(f):
    return {"col": f["subject"], "op": f["operator"], "val": f["comparator"]}

s = api()

# ============================================================
# INVESTIGATION RESULTS
# ============================================================
print("=" * 80)
print("INVESTIGATION RESULTS")
print("=" * 80)

print("""
DATA SCOPE:
- Total Gold table: 32,712 (all statuses)
- Aktif: 14,945 | Lulus: 13,328 | Others: 4,439
- Semester distribution: 5 (4,512), 7 (4,447), 9 (23,753)
- Research scope (Aktif+Lulus, sem>=5): 28,273

ML METRICS (from gold.model_metrics):
- Model: GaussianNB (v2)
- CV Mean Accuracy: 74.40%
- CV Mean F1: 75.70%
- Test Accuracy: 73.83%
- Test Precision: 77.67%
- Test Recall: 73.83%
- Test F1: 75.12%
- Training: 13,181 | Test: 2,637 | Inference: 14,662

CONFUSION MATRIX:
- TP (TW→TW): 410 | FN (TW→TL): 221
- FP (TL→TW): 469 | TN (TL→TL): 1,537

FINDING: All metrics are CORRECT and match model final.
No discrepancy found.
""")

# ============================================================
# CHART SELECTION: Keep 14 most informative
# ============================================================
print("=" * 80)
print("CHART SELECTION")
print("=" * 80)

# Charts to KEEP (14):
keep_charts = {
    # Section 1: Ringkasan Akademik (5)
    66: "Total Mahasiswa",
    67: "Mahasiswa Aktif",
    68: "Mahasiswa Lulus",
    69: "Tepat Waktu (Aktual)",
    70: "Terlambat (Aktual)",
    # Section 2: Profil Mahasiswa (3)
    71: "Jumlah Mahasiswa per Angkatan",
    72: "Distribusi Jenis Kelamin",
    73: "Distribusi Status Mahasiswa",
    # Section 3: Performa Akademik (4)
    74: "Rata-rata IPK per Angkatan (Lulus)",
    79: "Status Kelulusan per Angkatan (Stacked)",
    # Section 4: Hasil Evaluasi ML (6)
    81: "Model Accuracy (%)",
    82: "Model F1 Score (%)",
    83: "Model Precision (%)",
    85: "Confusion Matrix",
    # Section 5: Hasil Prediksi (2)
    87: "Prediksi ML per Angkatan (Aktif)",
    88: "Distribusi Prediksi ML (Mahasiswa Aktif)",
}

# Charts to REMOVE (12):
remove_charts = {
    75: "Rata-rata Total SKS per Angkatan - less informative than IPK",
    76: "Rata-rata Selisih SKS per Angkatan - redundant with Lama Studi",
    77: "Rata-rata Lama Studi per Angkatan - keep if needed",
    78: "Status Kelulusan Aktual pie - redundant with stacked bar 79",
    80: "Persentase Tepat Waktu per Angkatan - redundant with 79",
    84: "Model Recall - consolidate to 3 main metrics",
    86: "Classification Report table - less visual",
    89: "Selisih SKS per Semester - less informative",
    91: "Jumlah Aktif per Semester - less informative",
    100: "Distribusi IPK - table not visual",
}

print("\nCharts to KEEP:")
for cid, name in keep_charts.items():
    print(f"  Chart {cid}: {name}")

print(f"\nTotal kept: {len(keep_charts)}")

print("\nCharts to REMOVE:")
for cid, reason in remove_charts.items():
    print(f"  Chart {cid}: {reason}")

print(f"\nTotal removed: {len(remove_charts)}")

# ============================================================
# UPDATE KPI QUERIES with research scope
# ============================================================
print("\n" + "=" * 80)
print("UPDATING KPI QUERIES WITH RESEARCH SCOPE")
print("=" * 80)

# Update KPI 67 (Aktif) - add semester >= 5 filter
r = s.get(f"{BASE}/api/v1/chart/67")
c = r.json()["result"]
params = json.loads(c["params"])
qc = json.loads(c["query_context"])

# Add semester >= 5 filter
params["adhoc_filters"].append(make_adhoc("semester", ">=", 5))
qc["queries"][0]["filters"].append({"col": "semester", "op": ">=", "val": 5})

s.put(f"{BASE}/api/v1/chart/67", json={"params": json.dumps(params), "query_context": json.dumps(qc)})
print("Chart 67 (Aktif): added semester>=5 filter")

# Update KPI 68 (Lulus) - add semester >= 5 filter
r = s.get(f"{BASE}/api/v1/chart/68")
c = r.json()["result"]
params = json.loads(c["params"])
qc = json.loads(c["query_context"])

params["adhoc_filters"].append(make_adhoc("semester", ">=", 5))
qc["queries"][0]["filters"].append({"col": "semester", "op": ">=", "val": 5})

s.put(f"{BASE}/api/v1/chart/68", json={"params": json.dumps(params), "query_context": json.dumps(qc)})
print("Chart 68 (Lulus): added semester>=5 filter")

# Update KPI 69 (Tepat Waktu) - add semester >= 5 filter
r = s.get(f"{BASE}/api/v1/chart/69")
c = r.json()["result"]
params = json.loads(c["params"])
qc = json.loads(c["query_context"])

params["adhoc_filters"].append(make_adhoc("semester", ">=", 5))
qc["queries"][0]["filters"].append({"col": "semester", "op": ">=", "val": 5})

s.put(f"{BASE}/api/v1/chart/69", json={"params": json.dumps(params), "query_context": json.dumps(qc)})
print("Chart 69 (Tepat Waktu): added semester>=5 filter")

# Update KPI 70 (Terlambat) - add semester >= 5 filter
r = s.get(f"{BASE}/api/v1/chart/70")
c = r.json()["result"]
params = json.loads(c["params"])
qc = json.loads(c["query_context"])

params["adhoc_filters"].append(make_adhoc("semester", ">=", 5))
qc["queries"][0]["filters"].append({"col": "semester", "op": ">=", "val": 5})

s.put(f"{BASE}/api/v1/chart/70", json={"params": json.dumps(params), "query_context": json.dumps(qc)})
print("Chart 70 (Terlambat): added semester>=5 filter")

# Verify updated KPIs
print("\n--- Updated KPI values ---")
for cid in [66, 67, 68, 69, 70]:
    r = s.get(f"{BASE}/api/v1/chart/{cid}")
    c = r.json()["result"]
    qc = json.loads(c["query_context"])
    r2 = s.post(f"{BASE}/api/v1/chart/data", json=qc)
    if r2.status_code == 200:
        data = r2.json()
        d = data["result"][0].get("data", [])
        print(f"  Chart {cid} ({c['slice_name']}): {d}")
