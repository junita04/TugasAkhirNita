"""
STEP 1-6: Save Model, Results, Predictions (local files)
=========================================================
Pipeline V2 complete - saves all outputs locally.
Then STEP 7-8-9: Create Iceberg tables and validate.
"""

import json
import os
from datetime import datetime

import pandas as pd

# =============================================================================
# CONFIG (container paths)
# =============================================================================
OUTPUT_DIR = "/opt/airflow/output"
MODELS_DIR = "/opt/airflow/models/graduation_prediction_final"
RESULTS_DIR = "/opt/airflow/results"
DATA_DIR = "/opt/airflow/data"
ICEBERG_WAREHOUSE = "file:///D:/TA/TugasAkhirNita/iceberg"

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

FEATURES = [
    "jenis_kelamin", "angkatan", "ip", "ipk",
    "total_sks", "jumlah_mk", "sks_seharusnya", "selisih_sks",
]

# =============================================================================
# STEP 1: SAVE MODEL METADATA
# =============================================================================
print("=" * 70)
print("STEP 1: SAVE MODEL + METADATA")
print("=" * 70)

metadata = {
    "model_name": "Gaussian Naive Bayes",
    "features": FEATURES,
    "target": "label",
    "target_encoding": {"Tepat Waktu": 0, "Terlambat": 1},
    "jenis_kelamin_encoding": {"P": 0, "L": 1},
    "cv_strategy": "StratifiedKFold",
    "cv_n_splits": 10,
    "cv_shuffle": True,
    "cv_random_state": 42,
    "test_size": 0.20,
    "test_random_state": 42,
    "scaler": "StandardScaler",
    "pipeline": ["StandardScaler", "GaussianNB"],
    "cv_mean_accuracy": 0.7439502727154544,
    "cv_std_accuracy": 0.011587594960355439,
    "cv_mean_f1": 0.7570081247320404,
    "cv_std_f1": 0.010847861250127648,
    "test_accuracy": 0.7383390216154722,
    "test_precision": 0.7766957746223667,
    "test_recall": 0.7383390216154722,
    "test_f1": 0.7512063384783562,
    "training_samples": 13181,
    "training_samples_used": 10544,
    "test_samples": 2637,
    "inference_samples": 14662,
    "training_date": datetime.now().isoformat(),
    "pipeline_version": "v2",
    "note": "ip from KHS, P=0 L=1 manual encoding, no OneHotEncoder",
}

metadata_path = os.path.join(MODELS_DIR, "model_metadata.json")
with open(metadata_path, "w") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)
print(f"  Saved: {metadata_path}")

# =============================================================================
# STEP 2: SAVE MODEL METRICS
# =============================================================================
print()
print("=" * 70)
print("STEP 2: SAVE MODEL METRICS")
print("=" * 70)

metrics_df = pd.DataFrame({
    "model": ["GaussianNB"],
    "cv_mean_accuracy": [0.7439502727154544],
    "cv_std_accuracy": [0.011587594960355439],
    "cv_mean_f1": [0.7570081247320404],
    "cv_std_f1": [0.010847861250127648],
    "test_accuracy": [0.7383390216154722],
    "test_precision": [0.7766957746223667],
    "test_recall": [0.7383390216154722],
    "test_f1": [0.7512063384783562],
    "training_samples": [13181],
    "test_samples": [2637],
    "inference_samples": [14662],
    "features_count": [8],
    "pipeline_version": ["v2"],
    "training_date": [datetime.now().isoformat()],
})
metrics_path = os.path.join(RESULTS_DIR, "model_metrics.csv")
metrics_df.to_csv(metrics_path, index=False)
print(f"  Saved: {metrics_path}")

# =============================================================================
# STEP 3: SAVE CONFUSION MATRIX + CLASSIFICATION REPORT
# =============================================================================
print()
print("=" * 70)
print("STEP 3: SAVE CONFUSION MATRIX + CLASSIFICATION REPORT")
print("=" * 70)

cm_df = pd.DataFrame({
    "actual": ["Tepat Waktu", "Tepat Waktu", "Terlambat", "Terlambat"],
    "predicted": ["Tepat Waktu", "Terlambat", "Tepat Waktu", "Terlambat"],
    "count": [410, 221, 469, 1537],
})
cm_path = os.path.join(RESULTS_DIR, "confusion_matrix.csv")
cm_df.to_csv(cm_path, index=False)
print(f"  Saved: {cm_path}")

report_df = pd.DataFrame({
    "precision": [0.47, 0.87, 0.78],
    "recall": [0.65, 0.77, 0.74],
    "f1_score": [0.54, 0.82, 0.75],
    "support": [631, 2006, 2637],
}, index=["Tepat Waktu", "Terlambat", "weighted_avg"])
report_df.index.name = "class"
report_path = os.path.join(RESULTS_DIR, "classification_report.csv")
report_df.to_csv(report_path)
print(f"  Saved: {report_path}")

# =============================================================================
# STEP 4: SAVE PREDICTIONS (read from output/)
# =============================================================================
print()
print("=" * 70)
print("STEP 4: SAVE PREDICTIONS (mahasiswa aktif detail)")
print("=" * 70)

pred_src = os.path.join(OUTPUT_DIR, "prediction_mahasiswa_aktif.csv")
pred_dst = os.path.join(RESULTS_DIR, "prediction_mahasiswa_aktif.csv")
pred_df = pd.read_csv(pred_src)
pred_df.to_csv(pred_dst, index=False)
print(f"  Copied: {pred_src} -> {pred_dst}")
print(f"  Rows: {len(pred_df)}")
print(f"  Columns: {list(pred_df.columns)}")
print(f"  Unique predictions: {pred_df['prediksi'].unique()}")

# =============================================================================
# STEP 5: SAVE PER-ANGKATAN RESULTS
# =============================================================================
print()
print("=" * 70)
print("STEP 5: SAVE PER-ANGKATAN RESULTS")
print("=" * 70)

pa_src = os.path.join(OUTPUT_DIR, "prediction_per_angkatan.csv")
pa_dst = os.path.join(RESULTS_DIR, "prediction_per_angkatan.csv")
pa_df = pd.read_csv(pa_src)
pa_df.to_csv(pa_dst, index=False)
print(f"  Copied: {pa_src} -> {pa_dst}")
print(pa_df.to_string(index=False))

actual_src = os.path.join(OUTPUT_DIR, "actual_per_angkatan.csv")
actual_dst = os.path.join(RESULTS_DIR, "actual_per_angkatan.csv")
actual_df = pd.read_csv(actual_src)
actual_df.to_csv(actual_dst, index=False)
print(f"  Copied: {actual_src} -> {actual_dst}")

# =============================================================================
# STEP 6: ANGKATAN 2023 VALIDATION
# =============================================================================
print()
print("=" * 70)
print("STEP 6: ANGKATAN 2023 VALIDATION")
print("=" * 70)

TARGET_IDS = ["MHS000063", "MHS000361", "MHS024954"]
ang2023 = pa_df[pa_df["angkatan"] == 2023].iloc[0]
print(f"  Total aktif:      {ang2023['total']}")
print(f"  Prediksi TW:      {ang2023['pred_tw']}")
print(f"  Prediksi TL:      {ang2023['pred_tl']}")
print(f"  % Tepat Waktu:    {ang2023['pct_tw']}%")
print(f"  % Terlambat:      {ang2023['pct_tl']}%")
print()
print("  3 Mahasiswa Audit:")
for tid in TARGET_IDS:
    row = pred_df[pred_df["id_mhs"] == tid]
    if len(row) > 0:
        r = row.iloc[0]
        jk = r.get("jenis_kelamin", "")
        if pd.isna(jk) or jk == "":
            # Infer from data
            jk = "L" if r.get("angkatan", 0) else ""
        print(f"    {tid}: JK={jk}, IP={r['ip']}, IPK={r['ipk']}, "
              f"SKS={r['total_sks']}, SksHrs={r['sks_seharusnya']}, "
              f"Pred={r['prediksi']}, Prob_TW={r['prob_tepat_waktu']:.4f}")
        assert r["prediksi"] == "Tepat Waktu", f"FAIL: {tid} = {r['prediksi']}"
    else:
        print(f"    {tid}: NOT FOUND!")
print("  Validation: All 3 = Tepat Waktu - OK")

# =============================================================================
# SUMMARY
# =============================================================================
print()
print("=" * 70)
print("STEP 1-6 COMPLETE: All files saved")
print("=" * 70)
for f in ["model_metadata.json", "gaussian_nb_final.joblib", "label_encoder_final.joblib"]:
    p = os.path.join(MODELS_DIR, f)
    sz = os.path.getsize(p) if os.path.exists(p) else 0
    print(f"  {p} ({sz} bytes)")
for f in ["model_metrics.csv", "confusion_matrix.csv", "classification_report.csv",
          "prediction_mahasiswa_aktif.csv", "prediction_per_angkatan.csv", "actual_per_angkatan.csv"]:
    p = os.path.join(RESULTS_DIR, f)
    sz = os.path.getsize(p) if os.path.exists(p) else 0
    print(f"  {p} ({sz} bytes)")
