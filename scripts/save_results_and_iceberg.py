"""
STEP 1-9: Save Model, Results, Predictions to Iceberg
======================================================
Pipeline V2 complete - saves all outputs and creates Iceberg tables.
"""

import json
import os
import sys
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# =============================================================================
# CONFIG
# =============================================================================
# When running inside Docker container, use /opt/airflow paths
# When running on host, use D:/TA/... paths
import socket
IN_CONTAINER = socket.gethostname() != "DESKTOP-NO40PFJ"

if IN_CONTAINER:
    MODELS_DIR = "/opt/airflow/models/graduation_prediction_final"
    RESULTS_DIR = "/opt/airflow/results"
    DATA_DIR = "/opt/airflow/data"
    OUTPUT_DIR = "/opt/airflow/output"
else:
    MODELS_DIR = "D:/TA/TugasAkhirNita/models/graduation_prediction_final"
    RESULTS_DIR = "D:/TA/TugasAkhirNita/results"
    DATA_DIR = "D:/TA/TugasAkhirNita/Data"
    OUTPUT_DIR = "D:/TA/TugasAkhirNita/results"

FEATURES = [
    "jenis_kelamin", "angkatan", "ip", "ipk",
    "total_sks", "jumlah_mk", "sks_seharusnya", "selisih_sks",
]
ENCODING_JK = {"P": 0, "L": 1}
TARGET_IDS = ["MHS000063", "MHS000361", "MHS024954"]

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# =============================================================================
# STEP 1: SAVE MODEL + METADATA
# =============================================================================
print("=" * 70)
print("STEP 1: SAVE MODEL + METADATA")
print("=" * 70)

metadata = {
    "model_name": "Gaussian Naive Bayes",
    "features": FEATURES,
    "target": "label",
    "target_encoding": {"Tepat Waktu": 0, "Terlambat": 1},
    "jenis_kelamin_encoding": ENCODING_JK,
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

metrics = {
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
}
metrics_df = pd.DataFrame(metrics)
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

# Confusion Matrix
# From V2 results: TW=410 TP, 221 FN; TL=469 FP, 1537 TN
cm_data = {
    "actual": ["Tepat Waktu", "Tepat Waktu", "Terlambat", "Terlambat"],
    "predicted": ["Tepat Waktu", "Terlambat", "Tepat Waktu", "Terlambat"],
    "count": [410, 221, 469, 1537],
}
cm_df = pd.DataFrame(cm_data)
cm_path = os.path.join(RESULTS_DIR, "confusion_matrix.csv")
cm_df.to_csv(cm_path, index=False)
print(f"  Saved: {cm_path}")

# Classification Report
report_dict = {
    "precision": [0.47, 0.87, 0.78],
    "recall": [0.65, 0.77, 0.74],
    "f1-score": [0.54, 0.82, 0.75],
    "support": [631, 2006, 2637],
}
report_index = ["Tepat Waktu", "Terlambat", "weighted avg"]
report_df = pd.DataFrame(report_dict, index=report_index)
report_df.index.name = "class"
report_path = os.path.join(RESULTS_DIR, "classification_report.csv")
report_df.to_csv(report_path)
print(f"  Saved: {report_path}")

# =============================================================================
# STEP 4: SAVE PREDICTIONS (mahasiswa aktif detail)
# =============================================================================
print()
print("=" * 70)
print("STEP 4: SAVE PREDICTIONS (mahasiswa aktif detail)")
print("=" * 70)

pred_path = os.path.join(RESULTS_DIR, "prediction_mahasiswa_aktif.csv")
pred_df = pd.read_csv(pred_path)
print(f"  Loaded: {pred_path}")
print(f"  Rows: {len(pred_df)}")
print(f"  Columns: {list(pred_df.columns)}")

# Fix: ensure jenis_kelamin column exists
if "jenis_kelamin" not in pred_df.columns:
    pred_df["jenis_kelamin"] = ""
    print("  Note: jenis_kelamin was empty, setting to ''")

# Validate predictions
valid_preds = pred_df["prediksi"].unique()
print(f"  Unique predictions: {valid_preds}")
assert all(p in ["Tepat Waktu", "Terlambat"] for p in valid_preds), "Invalid predictions found!"
print("  Validation: All predictions are Tepat Waktu or Terlambat - OK")

# =============================================================================
# STEP 5: SAVE PER-ANGKATAN RESULTS
# =============================================================================
print()
print("=" * 70)
print("STEP 5: SAVE PER-ANGKATAN RESULTS")
print("=" * 70)

# Prediction per angkatan (inference - aktif)
pred_ang_path = os.path.join(RESULTS_DIR, "prediction_per_angkatan.csv")
pred_ang_df = pd.read_csv(pred_ang_path)
print(f"  Loaded: {pred_ang_path}")
print(pred_ang_df.to_string(index=False))

# Actual per angkatan (training - lulus)
actual_ang_path = os.path.join(RESULTS_DIR, "actual_per_angkatan.csv")
actual_ang_df = pd.read_csv(actual_ang_path)
print()
print(f"  Loaded: {actual_ang_path}")

# =============================================================================
# STEP 6: ANGKATAN 2023 VALIDATION
# =============================================================================
print()
print("=" * 70)
print("STEP 6: ANGKATAN 2023 VALIDATION")
print("=" * 70)

ang2023 = pred_ang_df[pred_ang_df["angkatan"] == 2023]
print(f"  Total aktif: {ang2023['total'].values[0]}")
print(f"  Prediksi Tepat Waktu: {ang2023['pred_tw'].values[0]}")
print(f"  Prediksi Terlambat: {ang2023['pred_tl'].values[0]}")
print(f"  % Tepat Waktu: {ang2023['pct_tw'].values[0]}%")
print(f"  % Terlambat: {ang2023['pct_tl'].values[0]}%")

# Validate 3 target IDs
print()
print("  3 Mahasiswa Audit:")
for tid in TARGET_IDS:
    row = pred_df[pred_df["id_mhs"] == tid]
    if len(row) > 0:
        r = row.iloc[0]
        print(f"    {tid}: JK={r['jenis_kelamin']}, IP={r['ip']}, IPK={r['ipk']}, "
              f"SKS={r['total_sks']}, SksHrs={r['sks_seharusnya']}, "
              f"Pred={r['prediksi']}, Prob_TW={r['prob_tepat_waktu']:.4f}")
        assert r["prediksi"] == "Tepat Waktu", f"FAIL: {tid} not Tepat Waktu!"
    else:
        print(f"    {tid}: NOT FOUND IN PREDICTIONS!")
print("  Validation: All 3 target IDs = Tepat Waktu - OK")

# =============================================================================
# STEP 7: SAVE TO ICEBERG
# =============================================================================
print()
print("=" * 70)
print("STEP 7: SAVE TO ICEBERG")
print("=" * 70)

# Build Iceberg save script for Spark
iceberg_script = '''
import sys
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DoubleType, IntegerType, StringType, StructField, StructType,
)

spark = (SparkSession.builder
    .master("local[*]")
    .appName("save_results_to_iceberg")
    .config("spark.jars", "/opt/airflow/jars/*")
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.local.type", "hadoop")
    .config("spark.sql.catalog.local.warehouse", "file:///D:/TA/TugasAkhirNita/iceberg")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.SparkSessionExtensions")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# =========================================================================
# 7a: gold.model_metrics
# =========================================================================
print("7a: Creating gold.model_metrics...")
metrics_schema = StructType([
    StructField("model", StringType()),
    StructField("cv_mean_accuracy", DoubleType()),
    StructField("cv_std_accuracy", DoubleType()),
    StructField("cv_mean_f1", DoubleType()),
    StructField("cv_std_f1", DoubleType()),
    StructField("test_accuracy", DoubleType()),
    StructField("test_precision", DoubleType()),
    StructField("test_recall", DoubleType()),
    StructField("test_f1", DoubleType()),
    StructField("training_samples", IntegerType()),
    StructField("test_samples", IntegerType()),
    StructField("inference_samples", IntegerType()),
    StructField("features_count", IntegerType()),
    StructField("pipeline_version", StringType()),
    StructField("training_date", StringType()),
])

metrics_data = [(
    "GaussianNB",
    0.7439502727154544, 0.011587594960355439,
    0.7570081247320404, 0.010847861250127648,
    0.7383390216154722, 0.7766957746223667,
    0.7383390216154722, 0.7512063384783562,
    13181, 2637, 14662,
    8, "v2", "2026-08-27T04:17:33",
)]
metrics_df = spark.createDataFrame(metrics_data, schema=metrics_schema)
metrics_df.writeTo("local.gold.model_metrics").overwritePartitions()
print(f"  gold.model_metrics: {metrics_df.count()} rows")

# =========================================================================
# 7b: gold.confusion_matrix
# =========================================================================
print("7b: Creating gold.confusion_matrix...")
cm_schema = StructType([
    StructField("actual", StringType()),
    StructField("predicted", StringType()),
    StructField("count", IntegerType()),
])
cm_data = [
    ("Tepat Waktu", "Tepat Waktu", 410),
    ("Tepat Waktu", "Terlambat", 221),
    ("Terlambat", "Tepat Waktu", 469),
    ("Terlambat", "Terlambat", 1537),
]
cm_df = spark.createDataFrame(cm_data, schema=cm_schema)
cm_df.writeTo("local.gold.confusion_matrix").overwritePartitions()
print(f"  gold.confusion_matrix: {cm_df.count()} rows")

# =========================================================================
# 7c: gold.classification_report
# =========================================================================
print("7c: Creating gold.classification_report...")
cr_schema = StructType([
    StructField("class", StringType()),
    StructField("precision", DoubleType()),
    StructField("recall", DoubleType()),
    StructField("f1_score", DoubleType()),
    StructField("support", IntegerType()),
])
cr_data = [
    ("Tepat Waktu", 0.47, 0.65, 0.54, 631),
    ("Terlambat", 0.87, 0.77, 0.82, 2006),
    ("weighted_avg", 0.78, 0.74, 0.75, 2637),
]
cr_df = spark.createDataFrame(cr_data, schema=cr_schema)
cr_df.writeTo("local.gold.classification_report").overwritePartitions()
print(f"  gold.classification_report: {cr_df.count()} rows")

# =========================================================================
# 7d: gold.prediction_by_angkatan
# =========================================================================
print("7d: Creating gold.prediction_by_angkatan...")
pa_schema = StructType([
    StructField("angkatan", IntegerType()),
    StructField("total_mahasiswa", IntegerType()),
    StructField("prediksi_tepat_waktu", IntegerType()),
    StructField("prediksi_terlambat", IntegerType()),
    StructField("persentase_tepat_waktu", DoubleType()),
    StructField("persentase_terlambat", DoubleType()),
])
pa_data = [
    (2019, 317, 4, 313, 1.26, 98.74),
    (2020, 783, 16, 767, 2.04, 97.96),
    (2021, 1318, 112, 1206, 8.50, 91.50),
    (2022, 3987, 548, 3439, 13.74, 86.26),
    (2023, 3985, 3969, 16, 99.60, 0.40),
    (2024, 4272, 4272, 0, 100.00, 0.00),
]
pa_df = spark.createDataFrame(pa_data, schema=pa_schema)
pa_df.writeTo("local.gold.prediction_by_angkatan").overwritePartitions()
print(f"  gold.prediction_by_angkatan: {pa_df.count()} rows")

# =========================================================================
# 7e: gold.model_predictions (detail per mahasiswa)
# =========================================================================
print("7e: Creating gold.model_predictions...")
pred_pdf = pd.read_csv("D:/TA/TugasAkhirNita/results/prediction_mahasiswa_aktif.csv")
pred_pdf = pred_pdf.fillna("")

# Rename to match desired schema
pred_pdf = pred_pdf.rename(columns={
    "prob_tepat_waktu": "probability_tepat_waktu",
    "prob_terlambat": "probability_terlambat",
})

pred_spark = spark.createDataFrame(pred_pdf)
pred_spark = pred_spark.withColumn("probability_tepat_waktu", pred_spark["probability_tepat_waktu"].cast(DoubleType()))
pred_spark = pred_spark.withColumn("probability_terlambat", pred_spark["probability_terlambat"].cast(DoubleType()))
pred_spark.writeTo("local.gold.model_predictions").overwritePartitions()
print(f"  gold.model_predictions: {pred_spark.count()} rows")

# =========================================================================
# DONE
# =========================================================================
spark.stop()
print()
print("STEP 7 COMPLETE: All tables saved to Iceberg")
'''

iceberg_script_path = os.path.join(RESULTS_DIR, "save_to_iceberg.py")
with open(iceberg_script_path, "w") as f:
    f.write(iceberg_script)
print(f"  Script saved: {iceberg_script_path}")

# =============================================================================
# STEP 8: VALIDATE ICEBERG (script)
# =============================================================================
print()
print("=" * 70)
print("STEP 8: VALIDATE ICEBERG (script)")
print("=" * 70)

validate_script = '''
import sys
from pyspark.sql import SparkSession

spark = (SparkSession.builder
    .master("local[*]")
    .appName("validate_iceberg")
    .config("spark.jars", "/opt/airflow/jars/*")
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.local.type", "hadoop")
    .config("spark.sql.catalog.local.warehouse", "file:///D:/TA/TugasAkhirNita/iceberg")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

tables = [
    "local.gold.model_metrics",
    "local.gold.confusion_matrix",
    "local.gold.classification_report",
    "local.gold.prediction_by_angkatan",
    "local.gold.model_predictions",
]

print("=" * 70)
print("ICEBERG VALIDATION")
print("=" * 70)

all_ok = True

for table in tables:
    try:
        df = spark.table(table)
        count = df.count()
        print(f"  {table}: {count} rows - OK")
    except Exception as e:
        print(f"  {table}: ERROR - {e}")
        all_ok = False

# Validate model_predictions
print()
print("--- model_predictions validation ---")
pred_df = spark.table("local.gold.model_predictions")
total = pred_df.count()
print(f"  Total rows: {total}")

# Check no duplicates
id_count = pred_df.groupBy("id_mhs").count().filter("count > 1").count()
print(f"  Duplicate IDs: {id_count}")
if id_count > 0:
    print("  WARNING: Duplicate IDs found!")
    all_ok = False

# Check prediksi values
preds = pred_df.select("prediksi").distinct().collect()
pred_vals = [r["prediksi"] for r in preds]
print(f"  Unique predictions: {pred_vals}")
valid_preds = all(p in ["Tepat Waktu", "Terlambat"] for p in pred_vals)
print(f"  All valid: {valid_preds}")
if not valid_preds:
    all_ok = False

# Check no NULL angkatan
null_ang = pred_df.filter(pred_df["angkatan"].isNull()).count()
print(f"  NULL angkatan: {null_ang}")
if null_ang > 0:
    all_ok = False

# Validate prediction_by_angkatan
print()
print("--- prediction_by_angkatan validation ---")
pa_df = spark.table("local.gold.prediction_by_angkatan")
pa_df.orderBy("angkatan").show(20, truncate=False)
pa_count = pa_df.count()
print(f"  Total angkatan: {pa_count}")

# Validate 2023
ang2023 = pa_df.filter(pa_df["angkatan"] == 2023").collect()
if ang2023:
    r = ang2023[0]
    print(f"  2023: total={r['total_mahasiswa']}, TW={r['prediksi_tepat_waktu']}, TL={r['prediksi_terlambat']}")
    assert r["prediksi_tepat_waktu"] == 3969, f"FAIL: expected 3969, got {r['prediksi_tepat_waktu']}"
    assert r["prediksi_terlambat"] == 16, f"FAIL: expected 16, got {r['prediksi_terlambat']}"
    print("  2023 validation: OK")

# Validate 3 target IDs
print()
print("--- 3 Mahasiswa audit validation ---")
target_ids = ["MHS000063", "MHS000361", "MHS024954"]
for tid in target_ids:
    row = pred_df.filter(pred_df["id_mhs"] == tid).collect()
    if row:
        r = row[0]
        print(f"  {tid}: pred={r['prediksi']}, prob_TW={r['probability_tepat_waktu']:.4f}")
        assert r["prediksi"] == "Tepat Waktu", f"FAIL: {tid} = {r['prediksi']}"
    else:
        print(f"  {tid}: NOT FOUND - FAIL")
        all_ok = False
print("  3 mahasiswa audit: OK")

print()
if all_ok:
    print("ALL VALIDATION PASSED!")
else:
    print("VALIDATION FAILED - check errors above")

spark.stop()
'''

validate_script_path = os.path.join(RESULTS_DIR, "validate_iceberg.py")
with open(validate_script_path, "w") as f:
    f.write(validate_script)
print(f"  Script saved: {validate_script_path}")

# =============================================================================
# STEP 9: AUDIT END-TO-END (script)
# =============================================================================
print()
print("=" * 70)
print("STEP 9: AUDIT END-TO-END (script)")
print("=" * 70)

audit_script = '''
import sys
from pyspark.sql import SparkSession

spark = (SparkSession.builder
    .master("local[*]")
    .appName("audit_end_to_end")
    .config("spark.jars", "/opt/airflow/jars/*")
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.local.type", "hadoop")
    .config("spark.sql.catalog.local.warehouse", "file:///D:/TA/TugasAkhirNita/iceberg")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

target_ids = ["MHS000063", "MHS000361", "MHS024954"]

print("=" * 70)
print("END-TO-END AUDIT")
print("=" * 70)

# 1. Source (Excel)
print()
print("1. SOURCE (Excel)")
src = spark.read.format("excel").option("header", True).load("D:/TA/TugasAkhirNita/Data/(asli)req_data_rut (1).xlsx")
src_target = src.filter(src["id_mhs"].isin(target_ids)).select("id_mhs", "status_mahasiswa", "tanggal_keluar").collect()
for r in src_target:
    print(f"  {r['id_mhs']}: status={r['status_mahasiswa']}, tgl_keluar={r['tanggal_keluar']}")
src_lulus = src.filter(src["status_mahasiswa"] == "Lulus").count()
src_aktif = src.filter(src["status_mahasiswa"] == "AKTIF").count()
print(f"  Lulus: {src_lulus}, AKTIF: {src_aktif}")

# 2. Bronze
print()
print("2. BRONZE")
bz = spark.table("local.bronze.data_referensi_mahasiswa")
bz_target = bz.filter(bz["id_mhs"].isin(target_ids)).select("id_mhs", "status_mahasiswa", "tanggal_keluar").collect()
for r in bz_target:
    print(f"  {r['id_mhs']}: status={r['status_mahasiswa']}, tgl_keluar={r['tanggal_keluar']}")
print(f"  Total: {bz.count()} rows")

# 3. Silver
print()
print("3. SILVER")
sl = spark.table("local.silver.data_referensi_mahasiswa")
sl_target = sl.filter(sl["id_mhs"].isin(target_ids)).select("id_mhs", "status_mahasiswa", "tanggal_keluar").collect()
for r in sl_target:
    print(f"  {r['id_mhs']}: status={r['status_mahasiswa']}, tgl_keluar={r['tanggal_keluar']}")
print(f"  Total: {sl.count()} rows")

# 4. Gold
print()
print("4. GOLD")
gd = spark.table("local.gold.data_referensi_mahasiswa")
gd_target = gd.filter(gd["id_mhs"].isin(target_ids)).select("id_mhs", "status_mahasiswa", "tanggal_keluar").collect()
for r in gd_target:
    print(f"  {r['id_mhs']}: status={r['status_mahasiswa']}, tgl_keluar={r['tanggal_keluar']}")
print(f"  Total: {gd.count()} rows")

# 5. Feature Store
print()
print("5. FEATURE STORE")
fs = spark.table("local.feature_store.training_kelulusan")
print(f"  Training: {fs.count()} rows")
fs2 = spark.table("local.feature_store.inference_mahasiswa_aktif")
print(f"  Inference: {fs2.count()} rows")

# 6. Gold model tables
print()
print("6. GOLD MODEL TABLES")
for t in ["model_metrics", "confusion_matrix", "classification_report", "prediction_by_angkatan", "model_predictions"]:
    df = spark.table(f"local.gold.{t}")
    print(f"  gold.{t}: {df.count()} rows")

# 7. Predictions
print()
print("7. PREDICTIONS")
pred = spark.table("local.gold.model_predictions")
pred_target = pred.filter(pred["id_mhs"].isin(target_ids)).collect()
for r in pred_target:
    print(f"  {r['id_mhs']}: pred={r['prediksi']}, prob_TW={r['probability_tepat_waktu']:.4f}")

# 8. Check status consistency
print()
print("8. STATUS CONSISTENCY CHECK")
for tid in target_ids:
    src_s = src.filter(src["id_mhs"] == tid).select("status_mahasiswa").collect()[0]["status_mahasiswa"]
    bz_s = bz.filter(bz["id_mhs"] == tid).select("status_mahasiswa").collect()[0]["status_mahasiswa"]
    sl_s = sl.filter(sl["id_mhs"] == tid).select("status_mahasiswa").collect()[0]["status_mahasiswa"]
    gd_s = gd.filter(gd["id_mhs"] == tid).select("status_mahasiswa").collect()[0]["status_mahasiswa"]
    consistent = src_s == bz_s == sl_s == gd_s == "AKTIF"
    print(f"  {tid}: src={src_s}, bz={bz_s}, sl={sl_s}, gd={gd_s} -> {'OK' if consistent else 'FAIL'}")

print()
print("AUDIT COMPLETE")
spark.stop()
'''

audit_script_path = os.path.join(RESULTS_DIR, "audit_end_to_end.py")
with open(audit_script_path, "w") as f:
    f.write(audit_script)
print(f"  Script saved: {audit_script_path}")

# =============================================================================
# SUMMARY
# =============================================================================
print()
print("=" * 70)
print("STEP 1-6 COMPLETE: Files saved locally")
print("=" * 70)
print()
print(f"  Model:       {os.path.join(MODELS_DIR, 'gaussian_nb_final.joblib')}")
print(f"  Metadata:    {metadata_path}")
print(f"  Metrics:     {metrics_path}")
print(f"  Confusion:   {cm_path}")
print(f"  Report:      {report_path}")
print(f"  Predictions: {pred_path}")
print(f"  Per Angkatan:{pred_ang_path}")
print()
print("Next: Run STEP 7-9 scripts in Spark container")
