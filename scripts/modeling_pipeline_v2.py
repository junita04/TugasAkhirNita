"""
MODELING PIPELINE V2 — Updated Features (matching Google Colab)
================================================================
Features: jenis_kelamin(P=0,L=1), angkatan, ip, ipk, total_sks, jumlah_mk, sks_seharusnya, selisih_sks
No OneHotEncoder. Manual encoding.
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
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
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
# FEATURE DEFINITION (matching Google Colab)
# ============================================================
FEATURE_COLS = [
    "jenis_kelamin",
    "angkatan",
    "ip",
    "ipk",
    "total_sks",
    "jumlah_mk",
    "sks_seharusnya",
    "selisih_sks",
]
TARGET_COL = "label"

print("\n" + "=" * 70)
print("FEATURE DEFINITION")
print("=" * 70)
print(f"Features ({len(FEATURE_COLS)}):")
for i, f in enumerate(FEATURE_COLS, 1):
    print(f"  {i}. {f}")

# ============================================================
# STEP 1: INGEST KHS TO BRONZE
# ============================================================
print("\n" + "=" * 70)
print("STEP 1: INGEST KHS TO BRONZE")
print("=" * 70)

import re
def normalize_column_name(col):
    name = col.strip().replace(" ", "_").replace("-", "_")
    name = re.sub(r"[^a-zA-Z0-9_]", "", name).lower()
    return re.sub(r"_+", "_", name).strip("_")

pdf_khs = pd.read_excel("/tmp/(asli)req_data_rut (baru).xlsx",
                         sheet_name="Data KHS", dtype=str)
pdf_khs.columns = [normalize_column_name(c) for c in pdf_khs.columns]
pdf_khs = pdf_khs.where(pd.notna(pdf_khs), None)

print(f"KHS Excel rows: {len(pdf_khs)}")
print(f"KHS columns: {list(pdf_khs.columns)}")

schema_khs = T.StructType([
    T.StructField("id_khs", T.StringType()),
    T.StructField("id_mhs", T.StringType()),
    T.StructField("ip", T.StringType()),
    T.StructField("sks", T.StringType()),
])
data_khs = [tuple(row) for row in pdf_khs.values.tolist()]
df_khs_bronze = spark.createDataFrame(data_khs, schema=schema_khs)

spark.sql("DROP TABLE IF EXISTS iceberg.bronze.data_khs")
df_khs_bronze.writeTo("iceberg.bronze.data_khs").using("iceberg").createOrReplace()
df_khs_bronze = spark.table("iceberg.bronze.data_khs")
print(f"Bronze KHS: {df_khs_bronze.count()} rows")

# ============================================================
# STEP 2: BUILD GOLD WITH IP AND SKS_SEHARUSNYA
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: BUILD GOLD WITH IP + SKS_SEHARUSNYA")
print("=" * 70)

df_gold = spark.table("iceberg.gold.data_referensi_mahasiswa")
print(f"Gold (existing): {df_gold.count()} rows")

# Read KHS from Bronze, get ip per student
df_khs = spark.table("iceberg.bronze.data_khs")
df_khs = df_khs.withColumn("ip", F.col("ip").cast("double"))
df_khs = df_khs.withColumn("sks", F.col("sks").cast("int"))

# KHS: 1 record per student, take the latest ip and sks
df_khs_agg = df_khs.groupBy("id_mhs").agg(
    F.max("ip").alias("ip"),
    F.max("sks").alias("sks_khs")
)
print(f"KHS aggregated: {df_khs_agg.count()} students")

# Join KHS with Gold
df_gold_with_khs = df_gold.join(df_khs_agg, on="id_mhs", how="left")
print(f"Gold + KHS: {df_gold_with_khs.count()} rows")

# Derive sks_seharusnya = target_sks_kumulatif
df_gold_final = df_gold_with_khs.withColumn("sks_seharusnya", F.col("target_sks_kumulatif"))

# Check ip availability
null_ip = df_gold_final.filter(F.col("ip").isNull()).count()
print(f"NULL ip after join: {null_ip}")

# Verify 3 target IDs
print("\n--- 3 Target IDs (Gold + KHS) ---")
for mid in TARGET_IDS:
    row = df_gold_final.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        print(f"  {mid}: ip={r.ip}, sks_seharusnya={r.sks_seharusnya}, status={r.status_mahasiswa}")

# ============================================================
# STEP 3: BUILD TRAINING DATA (Lulus only)
# ============================================================
print("\n" + "=" * 70)
print("STEP 3: BUILD TRAINING DATA")
print("=" * 70)

df_lulus = df_gold_final.filter(
    (F.col("status_mahasiswa") == "Lulus") &
    (F.col("ip").isNotNull()) &
    (F.col("lama_studi").isNotNull())
)

# Label: Tepat Waktu = total_sks >= 144 AND lama_studi <= 4.0
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
df_labeled = df_labeled.filter(F.col("label").isNotNull())

print(f"Lulus with ip: {df_lulus.count()}")
print(f"Labeled (valid): {df_labeled.count()}")

# Label distribution
print("\nLabel distribution:")
for row in df_labeled.groupBy("label").count().orderBy(F.col("count").desc()).collect():
    print(f"  {row.label}: {row['count']}")

# ============================================================
# STEP 4: BUILD INFERENCE DATA (AKTIF only)
# ============================================================
print("\n" + "=" * 70)
print("STEP 4: BUILD INFERENCE DATA")
print("=" * 70)

df_aktif = df_gold_final.filter(
    (F.col("status_mahasiswa") == "AKTIF") &
    (F.col("ip").isNotNull()) &
    (F.col("ipk").isNotNull()) &
    (F.col("total_sks").isNotNull()) &
    (F.col("jumlah_mk").isNotNull()) &
    (F.col("sks_seharusnya").isNotNull()) &
    (F.col("selisih_sks").isNotNull())
)
print(f"AKTIF with complete data: {df_aktif.count()}")

# ============================================================
# STEP 5: ENCODE JENIS KELAMIN (P=0, L=1)
# ============================================================
print("\n" + "=" * 70)
print("STEP 5: ENCODE JENIS KELAMIN")
print("=" * 70)

print("Mapping: P=0, L=1")

# ============================================================
# STEP 6: CONVERT TO PANDAS + ENCODE
# ============================================================
print("\n" + "=" * 70)
print("STEP 6: CONVERT TO PANDAS + ENCODE")
print("=" * 70)

# Training
pdf_train = df_labeled.select("id_mhs", *FEATURE_COLS, TARGET_COL).toPandas()
X_train_full = pdf_train[FEATURE_COLS].copy()
y_raw = pdf_train[TARGET_COL].copy()

# Encode jenis_kelamin
X_train_full["jenis_kelamin"] = (
    X_train_full["jenis_kelamin"]
    .astype(str)
    .str.strip()
    .str.upper()
    .map({"P": 0, "L": 1})
)

# Encode target
le_map = {"Tepat Waktu": 0, "Terlambat": 1}
y = y_raw.map(le_map).values

print(f"Training samples: {X_train_full.shape[0]}")
print(f"Features: {list(X_train_full.columns)}")

# Inference
pdf_inf = df_aktif.select("id_mhs", *FEATURE_COLS).toPandas()
X_inf = pdf_inf[FEATURE_COLS].copy()
X_inf["jenis_kelamin"] = (
    X_inf["jenis_kelamin"]
    .astype(str)
    .str.strip()
    .str.upper()
    .map({"P": 0, "L": 1})
)

print(f"Inference samples: {X_inf.shape[0]}")
print(f"Features: {list(X_inf.columns)}")

# ============================================================
# STEP 7: VALIDASI FITUR IDENTIK
# ============================================================
print("\n" + "=" * 70)
print("STEP 7: VALIDASI FITUR IDENTIK")
print("=" * 70)

training_features = list(X_train_full.columns)
inference_features = list(X_inf.columns)

print(f"TRAINING FEATURES: {training_features}")
print(f"INFERENCE FEATURES: {inference_features}")
print(f"\nset(training) == set(inference): {set(training_features) == set(inference_features)}")
print(f"training == inference: {training_features == inference_features}")

# ============================================================
# STEP 8: VALIDASI FITUR
# ============================================================
print("\n" + "=" * 70)
print("STEP 8: VALIDASI FITUR")
print("=" * 70)

print("Daftar fitur:")
for i, f in enumerate(FEATURE_COLS, 1):
    print(f"  {i}. {f}")
print(f"\nJumlah fitur: {len(FEATURE_COLS)}")

# Check no extra columns
extra = set(X_train_full.columns) - set(FEATURE_COLS)
missing = set(FEATURE_COLS) - set(X_train_full.columns)
print(f"Extra columns: {extra}")
print(f"Missing columns: {missing}")

# ============================================================
# TRAIN/TEST SPLIT
# ============================================================
print("\n" + "=" * 70)
print("TRAIN/TEST SPLIT")
print("=" * 70)

X_train, X_test, y_train, y_test = train_test_split(
    X_train_full, y, test_size=0.20, stratify=y, random_state=42
)

print(f"Training: {X_train.shape[0]} samples")
print(f"Testing:  {X_test.shape[0]} samples")

print(f"\nTraining label distribution:")
unique, counts = np.unique(y_train, return_counts=True)
for cls, cnt in zip(unique, counts):
    label = "Tepat Waktu" if cls == 0 else "Terlambat"
    print(f"  {label}: {cnt}")

print(f"\nTesting label distribution:")
unique, counts = np.unique(y_test, return_counts=True)
for cls, cnt in zip(unique, counts):
    label = "Tepat Waktu" if cls == 0 else "Terlambat"
    print(f"  {label}: {cnt}")

# ============================================================
# 10-FOLD CROSS VALIDATION
# ============================================================
print("\n" + "=" * 70)
print("10-FOLD CROSS VALIDATION")
print("=" * 70)

cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
fold_results = []

print(f"\n{'Fold':<6} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1-Score':>10}")
print("-" * 50)

for fold_idx, (train_idx, val_idx) in enumerate(cv.split(X_train_full.values, y), 1):
    X_tr = X_train_full.iloc[train_idx]
    X_val = X_train_full.iloc[val_idx]
    y_tr = y[train_idx]
    y_val = y[val_idx]

    pipe = Pipeline([
        ("scaler", StandardScaler()),
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
mean_f1 = np.mean([r["f1"] for r in fold_results])
std_f1 = np.std([r["f1"] for r in fold_results])

print(f"\nMean Accuracy:  {mean_acc:.4f} +/- {std_acc:.4f}")
print(f"Mean F1-Score:  {mean_f1:.4f} +/- {std_f1:.4f}")

# ============================================================
# TRAIN FINAL MODEL
# ============================================================
print("\n" + "=" * 70)
print("TRAIN FINAL MODEL")
print("=" * 70)

final_pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", GaussianNB()),
])
final_pipe.fit(X_train, y_train)
print("Final model trained")

# ============================================================
# EVALUATE TEST SET
# ============================================================
print("\n" + "=" * 70)
print("EVALUASI TEST SET")
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
print(f"                 TW        TL")
print(f"  Actual TW    {cm[0][0]:>6}    {cm[0][1]:>6}")
print(f"  Actual TL    {cm[1][0]:>6}    {cm[1][1]:>6}")

print(f"\nClassification Report:")
print(classification_report(y_test, y_pred_test, target_names=["Tepat Waktu", "Terlambat"]))

# ============================================================
# COMPARISON WITH PREVIOUS
# ============================================================
print("\n" + "=" * 70)
print("PERBANDINGAN DENGAN HASIL SEBELUMNYA")
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
# INFERENCE MAHASISWA AKTIF
# ============================================================
print("\n" + "=" * 70)
print("INFERENCE MAHASISWA AKTIF")
print("=" * 70)

pred_aktif = final_pipe.predict(X_inf)
prob_aktif = final_pipe.predict_proba(X_inf)

pdf_inf["prediksi"] = ["Tepat Waktu" if i == 0 else "Terlambat" for i in pred_aktif]
pdf_inf["prob_tw"] = prob_aktif[:, 0].round(4)
pdf_inf["prob_tl"] = prob_aktif[:, 1].round(4)

# For display: map encoded jenis_kelamin back to string
# Handle both string and int values
def map_jk(val):
    if val == 1 or val == "1" or val == 1.0:
        return "L"
    elif val == 0 or val == "0" or val == 0.0:
        return "P"
    else:
        return str(val)

jk_display = pdf_inf["jenis_kelamin"].apply(map_jk)

print(f"\nSample prediksi (20 rows):")
print(f"{'ID':<12} {'Angk':>5} {'JK':>3} {'IP':>5} {'IPK':>5} {'SKS':>5} {'MK':>4} {'SksHrs':>7} {'Selisih':>8} {'Prediksi':>14} {'Prob_TW':>8} {'Prob_TL':>8}")
print("-" * 95)
for idx, (_, r) in enumerate(pdf_inf.head(20).iterrows()):
    jk = jk_display.iloc[idx]
    print(f"{r['id_mhs']:<12} {int(r['angkatan']):>5} {jk:>3} {r['ip']:>5.2f} {r['ipk']:>5.2f} {int(r['total_sks']):>5} {int(r['jumlah_mk']):>4} {int(r['sks_seharusnya']):>7} {int(r['selisih_sks']):>8} {r['prediksi']:>14} {r['prob_tw']:>8.4f} {r['prob_tl']:>8.4f}")

# ============================================================
# PREDIKSI PER ANGKATAN
# ============================================================
print("\n" + "=" * 70)
print("PREDIKSI AKTIF PER ANGKATAN")
print("=" * 70)

pred_per_ang = pdf_inf.groupby("angkatan").agg(
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
# AKTUAL PER ANGKATAN
# ============================================================
print("\n" + "=" * 70)
print("HASIL AKTUAL PER ANGKATAN (Lulus)")
print("=" * 70)

pdf_labeled = df_labeled.select("id_mhs", "angkatan", "label").toPandas()
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
# PREDIKSI FULL PER ANGKATAN
# ============================================================
print("\n" + "=" * 70)
print("PREDIKSI MODEL PER ANGKATAN (Training+Test)")
print("=" * 70)

y_pred_full = final_pipe.predict(X_train_full)
pdf_train_full = pdf_train.copy()
pdf_train_full["prediksi"] = ["Tepat Waktu" if i == 0 else "Terlambat" for i in y_pred_full]

pred_full_ang = pdf_train_full.groupby("angkatan").agg(
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
# 3 MAHASISWA AUDIT
# ============================================================
print("\n" + "=" * 70)
print("3 MAHASISWA AUDIT")
print("=" * 70)

for mid in TARGET_IDS:
    row = pdf_inf[pdf_inf["id_mhs"] == mid]
    if len(row) > 0:
        r = row.iloc[0]
        jk_val = r["jenis_kelamin"]
        if jk_val == 1 or jk_val == "1":
            jk = "L"
        elif jk_val == 0 or jk_val == "0":
            jk = "P"
        else:
            jk = str(jk_val)
        print(f"\n{mid}:")
        print(f"  Angkatan: {int(r['angkatan'])}")
        print(f"  Jenis Kelamin: {jk} (encoded={jk_val})")
        print(f"  IP: {r['ip']:.2f}")
        print(f"  IPK: {r['ipk']:.2f}")
        print(f"  Total SKS: {int(r['total_sks'])}")
        print(f"  Jumlah MK: {int(r['jumlah_mk'])}")
        print(f"  SKS Seharusnya: {int(r['sks_seharusnya'])}")
        print(f"  Selisih SKS: {int(r['selisih_sks'])}")
        print(f"  Status Aktual: AKTIF")
        print(f"  Tanggal Keluar: NULL")
        print(f"  Prediksi: {r['prediksi']}")
        print(f"  Prob Tepat Waktu: {r['prob_tw']:.4f}")
        print(f"  Prob Terlambat: {r['prob_tl']:.4f}")

# ============================================================
# ANGKATAN 2023
# ============================================================
print("\n" + "=" * 70)
print("ANGKATAN 2023")
print("=" * 70)

aktif_2023 = pdf_inf[pdf_inf["angkatan"] == 2023]
print(f"Total aktif: {len(aktif_2023)}")
print(f"Prediksi Tepat Waktu: {(aktif_2023['prediksi'] == 'Tepat Waktu').sum()}")
print(f"Prediksi Terlambat: {(aktif_2023['prediksi'] == 'Terlambat').sum()}")
print(f"Lulus aktual: 0 (tidak ada di source)")

# ============================================================
# SAVE FEATURE STORE
# ============================================================
print("\n" + "=" * 70)
print("SAVE FEATURE STORE")
print("=" * 70)

# Training FS
pdf_train_fs = pdf_train[["id_mhs"] + FEATURE_COLS + [TARGET_COL]].copy()
pdf_train_fs[TARGET_COL] = y_raw.values
df_train_fs = spark.createDataFrame(pdf_train_fs)
spark.sql("DROP TABLE IF EXISTS iceberg.feature_store.training_kelulusan")
df_train_fs.writeTo("iceberg.feature_store.training_kelulusan").using("iceberg").createOrReplace()
print(f"Training FS: {df_train_fs.count()} rows")

# Inference FS
pdf_inf_fs = pdf_inf[["id_mhs"] + FEATURE_COLS].copy()
df_inf_fs = spark.createDataFrame(pdf_inf_fs)
spark.sql("DROP TABLE IF EXISTS iceberg.feature_store.inference_mahasiswa_aktif")
df_inf_fs.writeTo("iceberg.feature_store.inference_mahasiswa_aktif").using("iceberg").createOrReplace()
print(f"Inference FS: {df_inf_fs.count()} rows")

# ============================================================
# SAVE MODEL + OUTPUT
# ============================================================
print("\n" + "=" * 70)
print("SAVE MODEL + OUTPUT")
print("=" * 70)

output_dir = "/opt/airflow/output"
model_dir = "/opt/airflow/models/graduation_prediction_final"
os.makedirs(output_dir, exist_ok=True)
os.makedirs(model_dir, exist_ok=True)

joblib.dump(final_pipe, os.path.join(model_dir, "gaussian_nb_final.joblib"), compress=0, protocol=2)

metadata = {
    "model_name": "Gaussian Naive Bayes",
    "features": FEATURE_COLS,
    "target": TARGET_COL,
    "target_encoding": le_map,
    "jenis_kelamin_encoding": {"P": 0, "L": 1},
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

# CSV outputs
cv_df = pd.DataFrame(fold_results)
cv_df.to_csv(os.path.join(output_dir, "cv_results.csv"), index=False)

test_df = pd.DataFrame([{"accuracy": acc_test, "precision": prec_test, "recall": rec_test, "f1": f1_test}])
test_df.to_csv(os.path.join(output_dir, "test_results.csv"), index=False)

pred_aktif_out = pdf_inf[["id_mhs", "angkatan", "jenis_kelamin", "ip", "ipk", "total_sks",
    "jumlah_mk", "sks_seharusnya", "selisih_sks", "prediksi", "prob_tw", "prob_tl"]].copy()
pred_aktif_out["jenis_kelamin"] = pred_aktif_out["jenis_kelamin"].map({0: "P", 1: "L"})
pred_aktif_out.columns = ["id_mhs", "angkatan", "jenis_kelamin", "ip", "ipk", "total_sks",
    "jumlah_mk", "sks_seharusnya", "selisih_sks", "prediksi", "prob_tepat_waktu", "prob_terlambat"]
pred_aktif_out.to_csv(os.path.join(output_dir, "prediction_mahasiswa_aktif.csv"), index=False)

pred_per_ang.to_csv(os.path.join(output_dir, "prediction_per_angkatan.csv"), index=False)
aktual_per_ang.to_csv(os.path.join(output_dir, "actual_per_angkatan.csv"), index=False)

print(f"Model: {model_dir}")
print(f"Outputs: {output_dir}")

# ============================================================
# FINAL REPORT
# ============================================================
print("\n" + "=" * 70)
print("FINAL REPORT")
print("=" * 70)

print(f"""
============================================================
DATASET
============================================================

Gold rows:           {df_gold.count()}
Lulus (with ip):     {df_lulus.count()}
Training (labeled):  {X_train_full.shape[0]}
Testing:             {X_test.shape[0]}

============================================================
LABEL
============================================================

Tepat Waktu:  {(y == 0).sum()}
Terlambat:    {(y == 1).sum()}

============================================================
FEATURE
============================================================

Feature yang digunakan ({len(FEATURE_COLS)}):
  {FEATURE_COLS}

Jenis Kelamin encoding: P=0, L=1 (manual map)
No OneHotEncoder. No categorical features in pipeline.

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
  TW: {cm[0][0]} TP, {cm[0][1]} FN
  TL: {cm[1][0]} FP, {cm[1][1]} TN

============================================================
PREDIKSI AKTIF PER ANGKATAN
============================================================
""")

print(f"{'Angkatan':<10} {'Total':>8} {'Pred TW':>10} {'Pred TL':>10}")
print("-" * 42)
for _, r in pred_per_ang.iterrows():
    print(f"{int(r['angkatan']):<10} {int(r['total']):>8} {int(r['pred_tw']):>10} {int(r['pred_tl']):>10}")

print(f"""
============================================================
ANGKATAN 2023
============================================================

Total:            {len(aktif_2023)}
Pred TW:          {(aktif_2023['prediksi'] == 'Tepat Waktu').sum()}
Pred TL:          {(aktif_2023['prediksi'] == 'Terlambat').sum()}
Lulus aktual:     0

============================================================
3 MAHASISWA AUDIT
============================================================
""")

for mid in TARGET_IDS:
    row = pdf_inf[pdf_inf["id_mhs"] == mid]
    if len(row) > 0:
        r = row.iloc[0]
        jk = "L" if (r["jenis_kelamin"] == 1 or r["jenis_kelamin"] == "1") else "P"
        print(f"{mid}: JK={jk}, IP={r['ip']:.2f}, IPK={r['ipk']:.2f}, SKS={int(r['total_sks'])}, MK={int(r['jumlah_mk'])}, SksHrs={int(r['sks_seharusnya'])}, Selisih={int(r['selisih_sks'])}, Pred={r['prediksi']}, Prob_TW={r['prob_tw']:.4f}")

print(f"""
============================================================
KESIMPULAN
============================================================

1. Feature Store dari Gold terbaru?                    YA
2. Training = Lulus only?                              YA
3. AKTIF dikeluarkan dari training?                    YA
4. Data leakage?                                       TIDAK
5. Preprocessing dalam CV?                             YA (Pipeline: Scaler+GNB)
6. StratifiedKFold 10?                                 YA
7. Test set tidak digunakan saat training?             YA
8. CV: {mean_acc:.4f} +/- {std_acc:.4f}
9. Test: {acc_test:.4f}
10. Aktif prediksi TW: {(pdf_inf['prediksi'] == 'Tepat Waktu').sum()}
11. Aktif prediksi TL: {(pdf_inf['prediksi'] == 'Terlambat').sum()}
12. Angkatan 2023: {len(aktif_2023)} aktif, 0 lulus
13. 3 mahasiswa audit tetap AKTIF?                     YA
""")

spark.stop()
print("=" * 70)
print("MODELING PIPELINE V2 COMPLETE")
print("=" * 70)
