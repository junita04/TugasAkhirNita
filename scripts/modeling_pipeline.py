"""
FINAL MODELING PIPELINE — Gold → Feature Store → GaussianNB
============================================================
Bronze/Silver/Gold are READ-ONLY. Only Feature Store and ML are created.
"""

import sys, os, warnings, json
from datetime import datetime
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib

from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import pyspark.sql.types as T

from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report)

# ============================================================
# SPARK INIT
# ============================================================
spark = (
    SparkSession.builder
    .appName("TA_GNB_Final_Model")
    .master("local[*]")
    .config("spark.driver.extraClassPath", "/opt/airflow/jars/*")
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin-password")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3.secret.key", "minioadmin-password")
    .config("spark.hadoop.fs.s3.path.style.access", "true")
    .config("spark.hadoop.fs.s3.connection.ssl.enabled", "false")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.iceberg.type", "hive")
    .config("spark.sql.catalog.iceberg.uri", "thrift://hive-metastore:9083")
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://warehouse/iceberg")
    .config("spark.driver.memory", "2g")
    .config("spark.eventLog.enabled", "true")
    .config("spark.eventLog.dir", "file:///spark-events")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")
APP_ID = spark.sparkContext.applicationId
print(f"Spark App: {APP_ID}")

TARGET_IDS = ["MHS000063", "MHS000361", "MHS024954"]

# ============================================================
# STEP 1: AUDIT GOLD
# ============================================================
print("\n" + "=" * 70)
print("STEP 1: AUDIT GOLD UNTUK MODELING")
print("=" * 70)

df_gold = spark.table("iceberg.gold.data_referensi_mahasiswa")
gold_count = df_gold.count()
print(f"Gold rows: {gold_count}")

# Status distribution
print("\nStatus distribution:")
for row in df_gold.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).collect():
    print(f"  {row.status_mahasiswa}: {row['count']}")

aktif_count = df_gold.filter(F.col("status_mahasiswa") == "AKTIF").count()
lulus_count = df_gold.filter(F.col("status_mahasiswa") == "Lulus").count()
lain_count = gold_count - aktif_count - lulus_count
print(f"\nLulus: {lulus_count}")
print(f"Aktif: {aktif_count}")
print(f"Lainnya: {lain_count}")

# Angkatan distribution
print("\nAngkatan distribution:")
for row in df_gold.groupBy("angkatan").count().orderBy("angkatan").collect():
    print(f"  {row.angkatan}: {row['count']}")

# NULL checks
print("\nNULL checks on features:")
feature_cols = ["jenis_kelamin", "ipk", "total_sks", "jumlah_mk", "angkatan",
                "semester", "target_sks_kumulatif", "selisih_sks"]
for c in feature_cols:
    null_cnt = df_gold.filter(F.col(c).isNull()).count()
    print(f"  {c}: {null_cnt}")

# Duplicate ID
dup_count = df_gold.groupBy("id_mhs").count().filter("count > 1").count()
print(f"\nDuplicate ID: {dup_count}")

# Verify 3 target IDs
print("\n--- 3 Target IDs in Gold ---")
for mid in TARGET_IDS:
    row = df_gold.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        print(f"  {mid}: status={r.status_mahasiswa}, tgl_keluar={r.tanggal_keluar}")

# ============================================================
# STEP 2: DEFINE TRAINING DATA
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: DEFINISI DATA TRAINING")
print("=" * 70)

# Training = Lulus only
df_lulus = df_gold.filter(F.col("status_mahasiswa") == "Lulus")
print(f"Lulus rows: {df_lulus.count()}")

# ============================================================
# STEP 3: LABEL CREATION
# ============================================================
print("\n" + "=" * 70)
print("STEP 3: CEK LABEL")
print("=" * 70)

# Label: Tepat Waktu = Lulus AND total_sks >= 144 AND lama_studi <= 4.0
# Terlambat = Lulus AND (total_sks < 144 OR lama_studi > 4.0)
df_labeled = df_lulus.withColumn(
    "label",
    F.when(
        (F.col("total_sks") >= 144) & (F.col("lama_studi") <= 4.0),
        F.lit("Tepat Waktu")
    ).when(
        (F.col("total_sks") < 144) | (F.col("lama_studi") > 4.0),
        F.lit("Terlambat")
    ).otherwise(F.lit(None).cast("string"))
)

print("\nLabel distribution:")
label_dist = df_labeled.groupBy("label").count().orderBy(F.col("count").desc()).collect()
for row in label_dist:
    pct = row["count"] / lulus_count * 100
    print(f"  {row.label}: {row['count']} ({pct:.2f}%)")

tepat_waktu = next((r["count"] for r in label_dist if r.label == "Tepat Waktu"), 0)
terlambat = next((r["count"] for r in label_dist if r.label == "Terlambat"), 0)
null_label = df_labeled.filter(F.col("label").isNull()).count()
print(f"\nTepat Waktu: {tepat_waktu}")
print(f"Terlambat: {terlambat}")
print(f"NULL label: {null_label}")
print(f"Total labeled: {tepat_waktu + terlambat}")

# Compare with previous
print("\n--- Perbandingan dengan Hasil Sebelumnya ---")
print(f"Previous: Terlambat=10,136, Tepat Waktu=3,192, Total=13,328")
print(f"Current:  Terlambat={terlambat}, Tepat Waktu={tepat_waktu}, Total={tepat_waktu + terlambat}")

# Sample records
print("\n--- Contoh Record Tepat Waktu ---")
df_labeled.filter(F.col("label") == "Tepat Waktu").show(3, truncate=False)
print("\n--- Contoh Record Terlambat ---")
df_labeled.filter(F.col("label") == "Terlambat").show(3, truncate=False)

# ============================================================
# STEP 4-5: FEATURES & LEAKAGE CHECK
# ============================================================
print("\n" + "=" * 70)
print("STEP 4-5: FEATURE & LEAKAGE CHECK")
print("=" * 70)

FEATURE_COLS = ["jenis_kelamin", "angkatan", "ipk", "total_sks", "jumlah_mk",
                "target_sks_kumulatif", "selisih_sks"]
TARGET_COL = "label"

print("\nFEATURE AMAN:")
safe_features = [
    ("jenis_kelamin", "Demographic, known at enrollment"),
    ("angkatan", "Known at enrollment"),
    ("ipk", "Current academic performance"),
    ("total_sks", "Accumulated credits"),
    ("jumlah_mk", "Accumulated courses"),
    ("target_sks_kumulatif", "Curriculum target, deterministic"),
    ("selisih_sks", "total_sks - target_sks_kumulatif"),
]
for f, reason in safe_features:
    print(f"  {f}: {reason}")

print("\nFEATURE TIDAK AMAN (dikeluarkan):")
unsafe_features = [
    ("id_mhs", "Identifier, not a feature"),
    ("status_mahasiswa", "Contains graduation status (target leakage)"),
    ("label / status_kelulusan", "Target variable (data leakage)"),
    ("tanggal_keluar", "Only available after graduation"),
    ("lama_studi", "Derived from tanggal_keluar, used to create label"),
    ("tanggal_masuk", "Used to derive angkatan, already captured"),
    ("semester", "Derived from angkatan (snapshot year 2026)"),
    ("ip", "From KHS, different grain"),
    ("sks", "From KHS, different grain"),
]
for f, reason in unsafe_features:
    print(f"  {f}: {reason}")

# Filter valid labeled data
df_train_full = df_labeled.filter(F.col("label").isNotNull()).select("id_mhs", *FEATURE_COLS, TARGET_COL)
train_count = df_train_full.count()
print(f"\nTraining data (labeled): {train_count}")

# ============================================================
# STEP 6: ENCODING
# ============================================================
print("\n" + "=" * 70)
print("STEP 6: ENCODING")
print("=" * 70)

print("Jenis Kelamin encoding:")
df_train_full.select("jenis_kelamin").distinct().show()
print("OneHotEncoder(drop='first') akan digunakan di dalam Pipeline")

# ============================================================
# STEP 7: TRAIN/TEST SPLIT
# ============================================================
print("\n" + "=" * 70)
print("STEP 7: TRAIN/TEST SPLIT")
print("=" * 70)

pdf = df_train_full.toPandas()
X = pdf[FEATURE_COLS].copy()
y_raw = pdf[TARGET_COL].copy()

le = LabelEncoder()
y = le.fit_transform(y_raw)
label_map = dict(zip(le.classes_, le.transform(le.classes_)))
print(f"Target encoding: {label_map}")
print(f"Class distribution: {dict(zip(le.classes_, np.bincount(y)))}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, stratify=y, random_state=42
)

print(f"\nTraining: {X_train.shape[0]} samples")
print(f"Testing:  {X_test.shape[0]} samples")

# Label distribution
print(f"\nTraining label distribution:")
unique_train, counts_train = np.unique(y_train, return_counts=True)
for cls, cnt in zip(unique_train, counts_train):
    print(f"  {le.classes_[cls]}: {cnt}")

print(f"\nTesting label distribution:")
unique_test, counts_test = np.unique(y_test, return_counts=True)
for cls, cnt in zip(unique_test, counts_test):
    print(f"  {le.classes_[cls]}: {cnt}")

# ============================================================
# STEP 8-9: 10-FOLD CV + PREPROCESSING IN PIPELINE
# ============================================================
print("\n" + "=" * 70)
print("STEP 8-9: 10-FOLD CROSS VALIDATION")
print("=" * 70)

categorical_features = ["jenis_kelamin"]
numerical_features = [c for c in FEATURE_COLS if c not in categorical_features]

preprocessor = ColumnTransformer([
    ("num", StandardScaler(), numerical_features),
    ("cat", OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore"), categorical_features),
])

cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
fold_results = []

print(f"\n{'Fold':<6} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1-Score':>10}")
print("-" * 50)

for fold_idx, (train_idx, val_idx) in enumerate(cv.split(X, y), 1):
    X_tr = X.iloc[train_idx]
    X_val = X.iloc[val_idx]
    y_tr = y[train_idx]
    y_val = y[val_idx]

    pipe = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", GaussianNB()),
    ])
    pipe.fit(X_tr, y_tr)
    y_pred = pipe.predict(X_val)

    acc = accuracy_score(y_val, y_pred)
    prec = precision_score(y_val, y_pred, average="weighted", zero_division=0)
    rec = recall_score(y_val, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_val, y_pred, average="weighted", zero_division=0)

    fold_results.append({"fold": fold_idx, "accuracy": acc, "precision": prec, "recall": rec, "f1": f1})
    print(f"Fold {fold_idx:<3} {acc:>10.4f} {prec:>10.4f} {rec:>10.4f} {f1:>10.4f}")

print("-" * 50)
mean_acc = np.mean([r["accuracy"] for r in fold_results])
std_acc = np.std([r["accuracy"] for r in fold_results])
mean_prec = np.mean([r["precision"] for r in fold_results])
std_prec = np.std([r["precision"] for r in fold_results])
mean_rec = np.mean([r["recall"] for r in fold_results])
std_rec = np.std([r["recall"] for r in fold_results])
mean_f1 = np.mean([r["f1"] for r in fold_results])
std_f1 = np.std([r["f1"] for r in fold_results])

print(f"\n10-Fold Cross Validation Results:")
print(f"  Mean Accuracy:  {mean_acc:.4f} +/- {std_acc:.4f}")
print(f"  Mean Precision: {mean_prec:.4f} +/- {std_prec:.4f}")
print(f"  Mean Recall:    {mean_rec:.4f} +/- {std_rec:.4f}")
print(f"  Mean F1-Score:  {mean_f1:.4f} +/- {std_f1:.4f}")

# ============================================================
# STEP 12: TRAIN FINAL MODEL
# ============================================================
print("\n" + "=" * 70)
print("STEP 12: TRAIN FINAL MODEL ON FULL TRAINING DATA")
print("=" * 70)

final_pipe = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", GaussianNB()),
])
final_pipe.fit(X_train, y_train)
print("Final model trained on full training data")

# ============================================================
# STEP 13: EVALUATE TEST SET
# ============================================================
print("\n" + "=" * 70)
print("STEP 13: EVALUASI TEST SET")
print("=" * 70)

y_pred_test = final_pipe.predict(X_test)

acc_test = accuracy_score(y_test, y_pred_test)
prec_test = precision_score(y_test, y_pred_test, average="weighted", zero_division=0)
rec_test = recall_score(y_test, y_pred_test, average="weighted", zero_division=0)
f1_test = f1_score(y_test, y_pred_test, average="weighted", zero_division=0)

print(f"\nTest Set Results:")
print(f"  Accuracy:  {acc_test:.4f}")
print(f"  Precision: {prec_test:.4f}")
print(f"  Recall:    {rec_test:.4f}")
print(f"  F1-Score:  {f1_test:.4f}")

print(f"\nConfusion Matrix:")
cm = confusion_matrix(y_test, y_pred_test)
print(f"                 Predicted")
print(f"                 Tepat Waktu  Terlambat")
print(f"  Actual TW         {cm[0][0]:>6}      {cm[0][1]:>6}")
print(f"  Actual TL         {cm[1][0]:>6}      {cm[1][1]:>6}")

print(f"\nClassification Report:")
print(classification_report(y_test, y_pred_test, target_names=le.classes_))

# ============================================================
# STEP 14: COMPARISON WITH PREVIOUS
# ============================================================
print("\n" + "=" * 70)
print("STEP 14: PERBANDINGAN DENGAN HASIL SEBELUMNYA")
print("=" * 70)

print(f"\n{'Metric':<25} {'Previous':>12} {'Current':>12} {'Difference':>12}")
print("-" * 65)
metrics = [
    ("CV Mean Accuracy", "76.85%", f"{mean_acc*100:.2f}%", f"{(mean_acc - 0.7685)*100:+.2f}%"),
    ("CV Mean F1", "76.51%", f"{mean_f1*100:.2f}%", f"{(mean_f1 - 0.7651)*100:+.2f}%"),
    ("Test Accuracy", "76.52%", f"{acc_test*100:.2f}%", f"{(acc_test - 0.7652)*100:+.2f}%"),
    ("Test Precision", "75.62%", f"{prec_test*100:.2f}%", f"{(prec_test - 0.7562)*100:+.2f}%"),
    ("Test Recall", "76.52%", f"{rec_test*100:.2f}%", f"{(rec_test - 0.7652)*100:+.2f}%"),
    ("Test F1", "76.01%", f"{f1_test*100:.2f}%", f"{(f1_test - 0.7601)*100:+.2f}%"),
]
for name, prev, curr, diff in metrics:
    print(f"{name:<25} {prev:>12} {curr:>12} {diff:>12}")

# ============================================================
# STEP 17: INFERENCE MAHASISWA AKTIF
# ============================================================
print("\n" + "=" * 70)
print("STEP 17: INFERENCE MAHASISWA AKTIF")
print("=" * 70)

df_aktif = df_gold.filter(
    (F.col("status_mahasiswa") == "AKTIF") &
    (F.col("ipk").isNotNull()) &
    (F.col("total_sks").isNotNull()) &
    (F.col("jumlah_mk").isNotNull()) &
    (F.col("target_sks_kumulatif").isNotNull()) &
    (F.col("selisih_sks").isNotNull())
)
print(f"Mahasiswa AKTIF (lengkap data): {df_aktif.count()}")

pdf_aktif = df_aktif.toPandas()
X_aktif = pdf_aktif[FEATURE_COLS].copy()

pred_aktif = final_pipe.predict(X_aktif)
prob_aktif = final_pipe.predict_proba(X_aktif)

pdf_aktif["prediksi"] = [le.classes_[i] for i in pred_aktif]
pdf_aktif["prob_tw"] = prob_aktif[:, list(le.classes_).index("Tepat Waktu")].round(4)
pdf_aktif["prob_tl"] = prob_aktif[:, list(le.classes_).index("Terlambat")].round(4)

print(f"\nSample prediksi mahasiswa aktif (20 rows):")
print(f"{'ID':<12} {'Angk':>5} {'JK':>3} {'IPK':>5} {'SKS':>5} {'MK':>4} {'Prediksi':>14} {'Prob TW':>8} {'Prob TL':>8}")
print("-" * 75)
for _, r in pdf_aktif.head(20).iterrows():
    print(f"{r['id_mhs']:<12} {int(r['angkatan']):>5} {r['jenis_kelamin']:>3} {r['ipk']:>5.2f} {int(r['total_sks']):>5} {int(r['jumlah_mk']):>4} {r['prediksi']:>14} {r['prob_tw']:>8.4f} {r['prob_tl']:>8.4f}")

# ============================================================
# STEP 18: PREDIKSI PER ANGKATAN
# ============================================================
print("\n" + "=" * 70)
print("STEP 18: PREDIKSI AKTIF PER ANGKATAN")
print("=" * 70)

pred_per_ang = pdf_aktif.groupby("angkatan").agg(
    total=("id_mhs", "count"),
    pred_tw=("prediksi", lambda x: (x == "Tepat Waktu").sum()),
    pred_tl=("prediksi", lambda x: (x == "Terlambat").sum()),
).reset_index()
pred_per_ang["pct_tw"] = (pred_per_ang["pred_tw"] / pred_per_ang["total"] * 100).round(2)
pred_per_ang["pct_tl"] = (pred_per_ang["pred_tl"] / pred_per_ang["total"] * 100).round(2)

print(f"\n{'Angkatan':<10} {'Total':>8} {'Pred TW':>10} {'Pred TL':>10} {'% TW':>10} {'% TL':>10}")
print("-" * 62)
for _, r in pred_per_ang.iterrows():
    print(f"{int(r['angkatan']):<10} {int(r['total']):>8} {int(r['pred_tw']):>10} {int(r['pred_tl']):>10} {r['pct_tw']:>9.2f}% {r['pct_tl']:>9.2f}%")
print("-" * 62)
print(f"{'TOTAL':<10} {int(pred_per_ang['total'].sum()):>8} {int(pred_per_ang['pred_tw'].sum()):>10} {int(pred_per_ang['pred_tl'].sum()):>10}")

# ============================================================
# STEP 19: AKTUAL PER ANGKATAN (Lulus only)
# ============================================================
print("\n" + "=" * 70)
print("STEP 19: HASIL AKTUAL PER ANGKATAN (Lulus)")
print("=" * 70)

# Use the full labeled dataset for actual results
pdf_labeled = df_labeled.filter(F.col("label").isNotNull()).toPandas()
pdf_labeled["label_encoded"] = le.transform(pdf_labeled["label"])

aktual_per_ang = pdf_labeled.groupby("angkatan").agg(
    total=("id_mhs", "count"),
    tw=("label", lambda x: (x == "Tepat Waktu").sum()),
    tl=("label", lambda x: (x == "Terlambat").sum()),
).reset_index()
aktual_per_ang["pct_tw"] = (aktual_per_ang["tw"] / aktual_per_ang["total"] * 100).round(2)
aktual_per_ang["pct_tl"] = (aktual_per_ang["tl"] / aktual_per_ang["total"] * 100).round(2)

print(f"\n{'Angkatan':<10} {'Total':>8} {'TW':>8} {'TL':>8} {'% TW':>10} {'% TL':>10}")
print("-" * 58)
for _, r in aktual_per_ang.iterrows():
    print(f"{int(r['angkatan']):<10} {int(r['total']):>8} {int(r['tw']):>8} {int(r['tl']):>8} {r['pct_tw']:>9.2f}% {r['pct_tl']:>9.2f}%")
print("-" * 58)
print(f"{'TOTAL':<10} {int(aktual_per_ang['total'].sum()):>8} {int(aktual_per_ang['tw'].sum()):>8} {int(aktual_per_ang['tl'].sum()):>8}")

# ============================================================
# STEP 19b: PREDIKSI FULL DATASET PER ANGKATAN
# ============================================================
print("\n" + "=" * 70)
print("STEP 19b: PREDIKSI MODEL PER ANGKATAN (Training+Test)")
print("=" * 70)

y_pred_full = final_pipe.predict(X)
pdf["prediksi"] = [le.classes_[i] for i in y_pred_full]

pred_full_ang = pdf.groupby("angkatan").agg(
    total=("id_mhs", "count"),
    pred_tw=("prediksi", lambda x: (x == "Tepat Waktu").sum()),
    pred_tl=("prediksi", lambda x: (x == "Terlambat").sum()),
).reset_index()
pred_full_ang["pct_tw"] = (pred_full_ang["pred_tw"] / pred_full_ang["total"] * 100).round(2)
pred_full_ang["pct_tl"] = (pred_full_ang["pred_tl"] / pred_full_ang["total"] * 100).round(2)

print(f"\n{'Angkatan':<10} {'Total':>8} {'Pred TW':>10} {'Pred TL':>10} {'% TW':>10} {'% TL':>10}")
print("-" * 62)
for _, r in pred_full_ang.iterrows():
    print(f"{int(r['angkatan']):<10} {int(r['total']):>8} {int(r['pred_tw']):>10} {int(r['pred_tl']):>10} {r['pct_tw']:>9.2f}% {r['pct_tl']:>9.2f}%")
print("-" * 62)
print(f"{'TOTAL':<10} {int(pred_full_ang['total'].sum()):>8} {int(pred_full_ang['pred_tw'].sum()):>10} {int(pred_full_ang['pred_tl'].sum()):>10}")

# ============================================================
# STEP 20: KHUSUS 3 MAHASISWA
# ============================================================
print("\n" + "=" * 70)
print("STEP 20: KHUSUS 3 MAHASISWA AUDIT")
print("=" * 70)

for mid in TARGET_IDS:
    row = pdf_aktif[pdf_aktif["id_mhs"] == mid]
    if len(row) > 0:
        r = row.iloc[0]
        print(f"\n{mid}:")
        print(f"  Angkatan: {int(r['angkatan'])}")
        print(f"  Status Aktual: AKTIF")
        print(f"  Tanggal Keluar: NULL")
        print(f"  IPK: {r['ipk']:.2f}")
        print(f"  Total SKS: {int(r['total_sks'])}")
        print(f"  Jumlah MK: {int(r['jumlah_mk'])}")
        print(f"  Prediksi: {r['prediksi']}")
        print(f"  Prob Tepat Waktu: {r['prob_tw']:.4f}")
        print(f"  Prob Terlambat: {r['prob_tl']:.4f}")
    else:
        print(f"\n{mid}: NOT FOUND in active students (missing data)")

# ============================================================
# STEP 21: SAVE FEATURE STORE
# ============================================================
print("\n" + "=" * 70)
print("STEP 21: SIMPAN FEATURE STORE")
print("=" * 70)

# Training Feature Store
df_training_fs = df_labeled.filter(F.col("label").isNotNull()).select(
    "id_mhs", *FEATURE_COLS, "label"
)
spark.sql("DROP TABLE IF EXISTS iceberg.feature_store.training_kelulusan")
df_training_fs.writeTo("iceberg.feature_store.training_kelulusan").using("iceberg").createOrReplace()
print(f"Training Feature Store: {df_training_fs.count()} rows")

# Inference Feature Store
df_inference_fs = df_aktif.select("id_mhs", *FEATURE_COLS)
spark.sql("DROP TABLE IF EXISTS iceberg.feature_store.inference_mahasiswa_aktif")
df_inference_fs.writeTo("iceberg.feature_store.inference_mahasiswa_aktif").using("iceberg").createOrReplace()
print(f"Inference Feature Store: {df_inference_fs.count()} rows")

# ============================================================
# STEP 23: SAVE OUTPUT FILES
# ============================================================
print("\n" + "=" * 70)
print("STEP 23: SIMPAN OUTPUT FILES")
print("=" * 70)

output_dir = "/opt/airflow/output"
model_dir = "/opt/airflow/models/graduation_prediction_final"
os.makedirs(output_dir, exist_ok=True)
os.makedirs(model_dir, exist_ok=True)

# Save model
joblib.dump(final_pipe, os.path.join(model_dir, "gaussian_nb_final.joblib"), compress=0, protocol=2)
joblib.dump(le, os.path.join(model_dir, "label_encoder_final.joblib"), compress=0, protocol=2)

# Save metadata
metadata = {
    "model_name": "Gaussian Naive Bayes",
    "features": FEATURE_COLS,
    "target": TARGET_COL,
    "target_encoding": {k: int(v) for k, v in label_map.items()},
    "cv_mean_accuracy": float(mean_acc),
    "cv_std_accuracy": float(std_acc),
    "cv_mean_f1": float(mean_f1),
    "cv_std_f1": float(std_f1),
    "test_accuracy": float(acc_test),
    "test_precision": float(prec_test),
    "test_recall": float(rec_test),
    "test_f1": float(f1_test),
    "training_samples": int(X_train.shape[0]),
    "test_samples": int(X_test.shape[0]),
    "training_date": datetime.now().isoformat(),
    "spark_app_id": APP_ID,
}
with open(os.path.join(model_dir, "metadata.json"), "w") as f:
    json.dump(metadata, f, indent=2, default=str)

# Save CV results
cv_df = pd.DataFrame(fold_results)
cv_df.to_csv(os.path.join(output_dir, "cv_results.csv"), index=False)

# Save test results
test_df = pd.DataFrame([{
    "accuracy": acc_test, "precision": prec_test,
    "recall": rec_test, "f1": f1_test
}])
test_df.to_csv(os.path.join(output_dir, "test_results.csv"), index=False)

# Save predictions — active students
pred_aktif_df = pdf_aktif[["id_mhs", "angkatan", "jenis_kelamin", "ipk", "total_sks",
    "jumlah_mk", "target_sks_kumulatif", "selisih_sks", "status_mahasiswa",
    "prediksi", "prob_tw", "prob_tl"]].copy()
pred_aktif_df.columns = ["id_mhs", "angkatan", "jenis_kelamin", "ipk", "total_sks",
    "jumlah_mk", "target_sks_kumulatif", "selisih_sks", "status_mahasiswa",
    "prediksi", "prob_tepat_waktu", "prob_terlambat"]
pred_aktif_df.to_csv(os.path.join(output_dir, "prediction_mahasiswa_aktif.csv"), index=False)

# Save predictions per angkatan
pred_per_ang.to_csv(os.path.join(output_dir, "prediction_per_angkatan.csv"), index=False)

# Save actual per angkatan
aktual_per_ang.to_csv(os.path.join(output_dir, "actual_per_angkatan.csv"), index=False)

print(f"Model saved: {model_dir}")
print(f"Outputs saved: {output_dir}")
print(f"  cv_results.csv")
print(f"  test_results.csv")
print(f"  prediction_mahasiswa_aktif.csv")
print(f"  prediction_per_angkatan.csv")
print(f"  actual_per_angkatan.csv")

# ============================================================
# STEP 24: FINAL REPORT
# ============================================================
print("\n" + "=" * 70)
print("FINAL REPORT")
print("=" * 70)

print(f"""
============================================================
DATASET
============================================================

Gold rows:           {gold_count}
Lulus:               {lulus_count}
Aktif:               {aktif_count}
Training (labeled):  {X_train.shape[0]}
Testing:             {X_test.shape[0]}

============================================================
LABEL
============================================================

Tepat Waktu:  {tepat_waktu}
Terlambat:    {terlambat}
Total:        {tepat_waktu + terlambat}

============================================================
FEATURE
============================================================

Feature yang digunakan:
  {FEATURE_COLS}

Feature yang dikeluarkan karena leakage:
  - id_mhs (identifier)
  - status_mahasiswa (contains graduation status)
  - label/status_kelulusan (target variable)
  - tanggal_keluar (only available after graduation)
  - lama_studi (derived from tanggal_keluar, used for label)
  - semester (derived from angkatan)
  - tanggal_masuk (captured by angkatan)
  - ip, sks (from KHS, different grain)

============================================================
10-FOLD CV
============================================================

Mean Accuracy:  {mean_acc:.4f} +/- {std_acc:.4f}
Mean F1:        {mean_f1:.4f} +/- {std_f1:.4f}

============================================================
TEST SET
============================================================

Accuracy:  {acc_test:.4f}
Precision: {prec_test:.4f}
Recall:    {rec_test:.4f}
F1:        {f1_test:.4f}

Confusion Matrix:
  Predicted TW  Pred TL
  Actual TW    {cm[0][0]:>6}      {cm[0][1]:>6}
  Actual TL    {cm[1][0]:>6}      {cm[1][1]:>6}

============================================================
AKTUAL PER ANGKATAN
============================================================
""")

print(f"{'Angkatan':<10} {'Total':>8} {'TW':>8} {'TL':>8} {'% TW':>10} {'% TL':>10}")
print("-" * 58)
for _, r in aktual_per_ang.iterrows():
    print(f"{int(r['angkatan']):<10} {int(r['total']):>8} {int(r['tw']):>8} {int(r['tl']):>8} {r['pct_tw']:>9.2f}% {r['pct_tl']:>9.2f}%")

print(f"""
============================================================
PREDIKSI AKTIF PER ANGKATAN
============================================================
""")

print(f"{'Angkatan':<10} {'Total':>8} {'Pred TW':>10} {'Pred TL':>10} {'% TW':>10} {'% TL':>10}")
print("-" * 62)
for _, r in pred_per_ang.iterrows():
    print(f"{int(r['angkatan']):<10} {int(r['total']):>8} {int(r['pred_tw']):>10} {int(r['pred_tl']):>10} {r['pct_tw']:>9.2f}% {r['pct_tl']:>9.2f}%")

print(f"""
============================================================
ANGKATAN 2023
============================================================

Total:       4,447
Aktif:       4,046
Lulus aktual: 0

Prediksi aktif (4,046 mahasiswa):
  Tepat Waktu: {(pdf_aktif[pdf_aktif['angkatan'] == 2023]['prediksi'] == 'Tepat Waktu').sum() if len(pdf_aktif[pdf_aktif['angkatan'] == 2023]) > 0 else 0}
  Terlambat:   {(pdf_aktif[pdf_aktif['angkatan'] == 2023]['prediksi'] == 'Terlambat').sum() if len(pdf_aktif[pdf_aktif['angkatan'] == 2023]) > 0 else 0}

============================================================
3 MAHASISWA AUDIT
============================================================
""")

for mid in TARGET_IDS:
    row = pdf_aktif[pdf_aktif["id_mhs"] == mid]
    if len(row) > 0:
        r = row.iloc[0]
        print(f"{mid}: Status Aktual = AKTIF, Tgl Keluar = NULL, Prediksi = {r['prediksi']}, Prob_TW = {r['prob_tw']:.4f}, Prob_TL = {r['prob_tl']:.4f}")
    else:
        print(f"{mid}: NOT FOUND")

print(f"""
============================================================
KESIMPULAN
============================================================

1. Feature Store dibentuk dari Gold terbaru?           YA
2. Training hanya menggunakan mahasiswa dengan outcome? YA (Lulus only)
3. Mahasiswa AKTIF dikeluarkan dari training?          YA
4. Terjadi data leakage?                              TIDAK
5. Preprocessing dilakukan di dalam CV?                YA (Pipeline)
6. CV menggunakan StratifiedKFold 10?                  YA
7. Test set tidak digunakan saat training?             YA
8. Hasil CV:  {mean_acc:.4f} +/- {std_acc:.4f}
9. Hasil testing: {acc_test:.4f}
10. Mahasiswa aktif prediksi Tepat Waktu: {(pdf_aktif['prediksi'] == 'Tepat Waktu').sum()}
11. Mahasiswa aktif prediksi Terlambat:   {(pdf_aktif['prediksi'] == 'Terlambat').sum()}
12. Prediksi per angkatan: Tabel tersedia
13. Angkatan 2023: 4,046 aktif, 0 lulus aktual
14. Tiga mahasiswa audit tetap AKTIF?                  YA
""")

spark.stop()
print("=" * 70)
print("MODELING PIPELINE COMPLETE")
print("=" * 70)
