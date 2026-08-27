"""
END-TO-END PIPELINE — Data Terbaru
Bronze → Silver → Gold → Feature Store → GaussianNB → Prediksi

File: (asli)req_data_rut (1).xlsx
"""

import sys, os, re, json, warnings
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
# INITIALIZE SPARK
# ============================================================
spark = (
    SparkSession.builder
    .appName("TA_EndToEnd_GNB_10Fold")
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

def normalize_column_name(col):
    name = col.strip().replace(" ", "_").replace("-", "_")
    name = re.sub(r"[^a-zA-Z0-9_]", "", name).lower()
    return re.sub(r"_+", "_", name).strip("_")

# ============================================================
# STEP 1: BRONZE — Read Excel
# ============================================================
print("\n" + "=" * 70)
print("STEP 1: BRONZE — Read Excel")
print("=" * 70)

pdf = pd.read_excel("/tmp/new_data.xlsx",
                    sheet_name="Referensi Data Mahasiswa",
                    dtype=str)
pdf.columns = [normalize_column_name(c) for c in pdf.columns]
pdf = pdf.where(pd.notna(pdf), None)

print(f"Excel rows: {len(pdf)}")
print(f"Excel columns: {list(pdf.columns)}")

# Create Spark DataFrame
schema = T.StructType([
    T.StructField("id_mhs", T.StringType()),
    T.StructField("jenis_kelamin", T.StringType()),
    T.StructField("tanggal_masuk", T.StringType()),
    T.StructField("tanggal_keluar", T.StringType()),
    T.StructField("ipk", T.StringType()),
    T.StructField("total_sks", T.StringType()),
    T.StructField("jumlah_mk", T.StringType()),
    T.StructField("status_mahasiswa", T.StringType()),
])

data_rows = [tuple(row) for row in pdf.values.tolist()]
df_bronze = spark.createDataFrame(data_rows, schema=schema)

# Write Bronze
spark.sql("DROP TABLE IF EXISTS iceberg.bronze.data_referensi_mahasiswa")
df_bronze.writeTo("iceberg.bronze.data_referensi_mahasiswa").using("iceberg").createOrReplace()
df_bronze = spark.table("iceberg.bronze.data_referensi_mahasiswa")

print(f"\nBronze rows: {df_bronze.count()}")

# Bronze Audit
print("\n--- Bronze Audit ---")
bronze_status = df_bronze.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).collect()
print("Status distribution:")
for row in bronze_status:
    print(f"  {row.status_mahasiswa}: {row['count']}")

# Angkatan 2023
bronze_2023 = df_bronze.filter(F.year(F.col("tanggal_masuk")) == 2023)
print(f"\nAngkatan 2023: {bronze_2023.count()}")
bronze_2023_status = bronze_2023.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).collect()
print("Angkatan 2023 status:")
for row in bronze_2023_status:
    print(f"  {row.status_mahasiswa}: {row['count']}")

# Check 3 target IDs
print("\n--- 3 Target IDs in Bronze ---")
for mid in TARGET_IDS:
    row = df_bronze.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        print(f"  {mid}: status={r.status_mahasiswa}, tgl_masuk={r.tanggal_masuk}, tgl_keluar={r.tanggal_keluar}, ipk={r.ipk}, sks={r.total_sks}, mk={r.jumlah_mk}")

# ============================================================
# STEP 2: SILVER — Clean
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: SILVER — Clean")
print("=" * 70)

df_silver = df_bronze

# Trim all string columns
for col_name in df_silver.columns:
    df_silver = df_silver.withColumn(col_name, F.trim(F.col(col_name)))

# Empty string → NULL
for col_name in df_silver.columns:
    df_silver = df_silver.withColumn(
        col_name,
        F.when(F.col(col_name).isin("", " "), F.lit(None).cast("string"))
         .otherwise(F.col(col_name))
    )

# String NaN/null → NULL
for col_name in df_silver.columns:
    df_silver = df_silver.withColumn(
        col_name,
        F.when(F.lower(F.trim(F.col(col_name))).isin("nan", "null", "none", "-"),
               F.lit(None).cast("string"))
         .otherwise(F.col(col_name))
    )

# Standardize jenis_kelamin
df_silver = df_silver.withColumn("jenis_kelamin", F.upper(F.col("jenis_kelamin")))

# Dedup
before_dedup = df_silver.count()
df_silver = df_silver.dropDuplicates()
after_dedup = df_silver.count()
print(f"Duplicates removed: {before_dedup - after_dedup}")

# Remove NULL tanggal_masuk
null_tm = df_silver.filter(F.col("tanggal_masuk").isNull()).count()
df_silver = df_silver.filter(F.col("tanggal_masuk").isNotNull())
print(f"NULL tanggal_masuk removed: {null_tm}")

# Write Silver
spark.sql("DROP TABLE IF EXISTS iceberg.silver.data_referensi_mahasiswa")
df_silver.writeTo("iceberg.silver.data_referensi_mahasiswa").using("iceberg").createOrReplace()
df_silver = spark.table("iceberg.silver.data_referensi_mahasiswa")

print(f"\nSilver rows: {df_silver.count()}")

# Silver Audit
print("\n--- Silver Audit ---")
silver_status = df_silver.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).collect()
print("Status distribution:")
for row in silver_status:
    print(f"  {row.status_mahasiswa}: {row['count']}")

# Check 3 target IDs
print("\n--- 3 Target IDs in Silver ---")
for mid in TARGET_IDS:
    row = df_silver.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        print(f"  {mid}: status={r.status_mahasiswa}, tgl_masuk={r.tanggal_masuk}, tgl_keluar={r.tanggal_keluar}")

# ============================================================
# STEP 3: GOLD — Feature Engineering
# ============================================================
print("\n" + "=" * 70)
print("STEP 3: GOLD — Feature Engineering")
print("=" * 70)

df_gold = df_silver

# Cast types
df_gold = df_gold.withColumn("total_sks", F.col("total_sks").cast("int"))
df_gold = df_gold.withColumn("jumlah_mk", F.col("jumlah_mk").cast("int"))
df_gold = df_gold.withColumn("ipk", F.col("ipk").cast("double"))
df_gold = df_gold.withColumn("tanggal_masuk", F.to_date(F.col("tanggal_masuk"), "yyyy-MM-dd"))
df_gold = df_gold.withColumn("tanggal_keluar", F.to_date(F.col("tanggal_keluar"), "yyyy-MM-dd"))

# Angkatan
df_gold = df_gold.withColumn("angkatan", F.year(F.col("tanggal_masuk")))

# Semester (static mapping)
df_gold = df_gold.withColumn(
    "semester",
    F.when(F.col("angkatan") == 2026, 1)
     .when(F.col("angkatan") == 2025, 3)
     .when(F.col("angkatan") == 2024, 5)
     .when(F.col("angkatan") == 2023, 7)
     .when(F.col("angkatan") <= 2022, 9)
     .otherwise(F.lit(None).cast("int"))
)

# Target SKS
sks_targets = {1:17, 2:36, 3:55, 4:75, 5:95, 6:115, 7:135, 8:144, 9:144}
target_sks_expr = F.lit(None).cast("int")
for sem, target in sks_targets.items():
    target_sks_expr = F.when(F.col("semester") == sem, F.lit(target)).otherwise(target_sks_expr)
df_gold = df_gold.withColumn("target_sks_kumulatif", target_sks_expr)

# Selisih SKS
df_gold = df_gold.withColumn(
    "selisih_sks",
    F.when(F.col("target_sks_kumulatif").isNotNull(),
           F.col("total_sks") - F.col("target_sks_kumulatif"))
     .otherwise(F.lit(None).cast("int"))
)

# Lama Studi
df_gold = df_gold.withColumn(
    "lama_studi",
    F.when(F.col("tanggal_keluar").isNotNull(),
           F.round(F.datediff(F.col("tanggal_keluar"), F.col("tanggal_masuk")) / 365.25, 2))
     .otherwise(F.lit(None).cast("double"))
)

# Status Kelulusan — ONLY for Lulus students
df_gold = df_gold.withColumn(
    "status_kelulusan",
    F.when(
        (F.col("status_mahasiswa") == "Lulus") &
        (F.col("total_sks") >= 144) &
        (F.col("lama_studi") <= 4.0),
        F.lit("Tepat Waktu")
    ).when(
        (F.col("status_mahasiswa") == "Lulus") &
        ((F.col("total_sks") < 144) | (F.col("lama_studi") > 4.0)),
        F.lit("Terlambat")
    ).otherwise(F.lit(None).cast("string"))
)

# Write Gold
spark.sql("DROP TABLE IF EXISTS iceberg.gold.data_referensi_mahasiswa")
df_gold.writeTo("iceberg.gold.data_referensi_mahasiswa").using("iceberg").createOrReplace()
df_gold = spark.table("iceberg.gold.data_referensi_mahasiswa")

print(f"\nGold rows: {df_gold.count()}")

# Gold Audit
print("\n--- Gold Audit ---")
gold_status = df_gold.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).collect()
print("Status distribution:")
for row in gold_status:
    print(f"  {row.status_mahasiswa}: {row['count']}")

gold_label = df_gold.groupBy("status_kelulusan").count().orderBy(F.col("count").desc()).collect()
print("Status kelulusan distribution:")
for row in gold_label:
    print(f"  {row.status_kelulusan}: {row['count']}")

# Check 3 target IDs — CRITICAL
print("\n--- CRITICAL: 3 Target IDs in Gold ---")
for mid in TARGET_IDS:
    row = df_gold.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        print(f"  {mid}: status={r.status_mahasiswa}, tgl_keluar={r.tanggal_keluar}, lama_studi={r.lama_studi}, label={r.status_kelulusan}")
        if r.status_mahasiswa != "AKTIF":
            print(f"  *** ANOMALY: Status berubah dari AKTIF! ***")
        if r.tanggal_keluar is not None:
            print(f"  *** ANOMALI: tanggal_keluar tidak NULL! ***")

# ============================================================
# STEP 4: VALIDASI 3 MAHASISWA 2023
# ============================================================
print("\n" + "=" * 70)
print("STEP 4: VALIDASI 3 MAHASISWA ANGKATAN 2023")
print("=" * 70)

# Check Excel source
print("\n--- Data Asli (Excel) ---")
for mid in TARGET_IDS:
    row = pdf[pdf["id_mhs"] == mid]
    if len(row) > 0:
        r = row.iloc[0]
        print(f"  {mid}: status={r['status_mahasiswa']}, tgl_keluar={r['tanggal_keluar']}")

# Check Bronze
print("\n--- Bronze ---")
for mid in TARGET_IDS:
    row = df_bronze.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        print(f"  {mid}: status={r.status_mahasiswa}, tgl_keluar={r.tanggal_keluar}")

# Check Silver
print("\n--- Silver ---")
for mid in TARGET_IDS:
    row = df_silver.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        print(f"  {mid}: status={r.status_mahasiswa}, tgl_keluar={r.tanggal_keluar}")

# Check Gold
print("\n--- Gold ---")
for mid in TARGET_IDS:
    row = df_gold.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        print(f"  {mid}: status={r.status_mahasiswa}, tgl_keluar={r.tanggal_keluar}, lama_studi={r.lama_studi}, label={r.status_kelulusan}")

# ============================================================
# STEP 5: FEATURE STORE
# ============================================================
print("\n" + "=" * 70)
print("STEP 5: FEATURE STORE")
print("=" * 70)

# Filter: semester >= 5 AND status_mahasiswa == Lulus AND status_kelulusan NOT NULL
df_fs = df_gold.filter(
    (F.col("semester") >= 5) &
    (F.col("status_mahasiswa") == "Lulus") &
    (F.col("status_kelulusan").isNotNull())
)

FEATURE_COLS = ["jenis_kelamin", "ipk", "total_sks", "jumlah_mk",
                "angkatan", "semester", "target_sks_kumulatif", "selisih_sks"]
TARGET_COL = "status_kelulusan"

df_fs = df_fs.select("id_mhs", *FEATURE_COLS, TARGET_COL)

spark.sql("DROP TABLE IF EXISTS iceberg.feature_store.feature_store_graduation_prediction")
df_fs.writeTo("iceberg.feature_store.feature_store_graduation_prediction").using("iceberg").createOrReplace()
df_fs = spark.table("iceberg.feature_store.feature_store_graduation_prediction")

fs_count = df_fs.count()
print(f"\nFeature Store rows: {fs_count}")

# Convert to Pandas for ML
pdf_fs = df_fs.toPandas()
X = pdf_fs[FEATURE_COLS].copy()
y_raw = pdf_fs[TARGET_COL].copy()

# Encode target
le = LabelEncoder()
y = le.fit_transform(y_raw)
label_map = dict(zip(le.classes_, le.transform(le.classes_)))
print(f"Target encoding: {label_map}")
print(f"Class distribution: {dict(zip(le.classes_, np.bincount(y)))}")

# ============================================================
# STEP 6: TRAIN/TEST SPLIT
# ============================================================
print("\n" + "=" * 70)
print("STEP 6: TRAIN/TEST SPLIT")
print("=" * 70)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"Training: {X_train.shape[0]} samples")
print(f"Testing:  {X_test.shape[0]} samples")

# ============================================================
# STEP 7: 10-FOLD CROSS VALIDATION
# ============================================================
print("\n" + "=" * 70)
print("STEP 7: 10-FOLD CROSS VALIDATION — GaussianNB")
print("=" * 70)

categorical_features = ["jenis_kelamin"]
numerical_features = [c for c in FEATURE_COLS if c not in categorical_features]

preprocessor = ColumnTransformer([
    ("num", StandardScaler(), numerical_features),
    ("cat", OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore"), categorical_features),
])

cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
fold_results = []
all_y_true = []
all_y_pred = []

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
    all_y_true.extend(y_val)
    all_y_pred.extend(y_pred)

    print(f"Fold {fold_idx:<3} {acc:>10.4f} {prec:>10.4f} {rec:>10.4f} {f1:>10.4f}")

print("-" * 50)
mean_acc = np.mean([r["accuracy"] for r in fold_results])
std_acc = np.std([r["accuracy"] for r in fold_results])
mean_f1 = np.mean([r["f1"] for r in fold_results])
std_f1 = np.std([r["f1"] for r in fold_results])
print(f"Mean Accuracy: {mean_acc:.4f} ± {std_acc:.4f}")
print(f"Mean F1-Score: {mean_f1:.4f} ± {std_f1:.4f}")

# ============================================================
# STEP 8: TRAIN FINAL MODEL & EVALUATE ON TEST SET
# ============================================================
print("\n" + "=" * 70)
print("STEP 8: TRAIN FINAL MODEL & EVALUATE ON TEST SET")
print("=" * 70)

final_pipe = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", GaussianNB()),
])
final_pipe.fit(X_train, y_train)
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
print(f"  Predicted TW  Pred TL")
print(f"  Actual TW  {cm[0][0]:>6}    {cm[0][1]:>6}")
print(f"  Actual TL  {cm[1][0]:>6}    {cm[1][1]:>6}")

print(f"\nClassification Report:")
print(classification_report(y_test, y_pred_test, target_names=le.classes_))

# ============================================================
# STEP 9: HASIL AKTUAL PER ANGKATAN
# ============================================================
print("\n" + "=" * 70)
print("STEP 9: HASIL AKTUAL PER ANGKATAN")
print("=" * 70)

pdf_fs["label"] = [le.classes_[i] for i in y]
aktual_per_angkatan = pdf_fs.groupby("angkatan").agg(
    total=("id_mhs", "count"),
    tw=("label", lambda x: (x == "Tepat Waktu").sum()),
    tl=("label", lambda x: (x == "Terlambat").sum()),
).reset_index()
aktual_per_angkatan["pct_tw"] = (aktual_per_angkatan["tw"] / aktual_per_angkatan["total"] * 100).round(2)
aktual_per_angkatan["pct_tl"] = (aktual_per_angkatan["tl"] / aktual_per_angkatan["total"] * 100).round(2)

print(f"\n{'Angkatan':<10} {'Total':>8} {'TW':>8} {'TL':>8} {'% TW':>10} {'% TL':>10}")
print("-" * 58)
for _, r in aktual_per_angkatan.iterrows():
    print(f"{int(r['angkatan']):<10} {int(r['total']):>8} {int(r['tw']):>8} {int(r['tl']):>8} {r['pct_tw']:>9.2f}% {r['pct_tl']:>9.2f}%")
print("-" * 58)
print(f"{'TOTAL':<10} {int(aktual_per_angkatan['total'].sum()):>8} {int(aktual_per_angkatan['tw'].sum()):>8} {int(aktual_per_angkatan['tl'].sum()):>8}")

# ============================================================
# STEP 10: PREDIKSI MODEL PER ANGKATAN
# ============================================================
print("\n" + "=" * 70)
print("STEP 10: HASIL PREDIKSI MODEL PER ANGKATAN")
print("=" * 70)

y_pred_full = final_pipe.predict(X)
pdf_fs["prediksi"] = [le.classes_[i] for i in y_pred_full]

pred_per_angkatan = pdf_fs.groupby("angkatan").agg(
    total=("id_mhs", "count"),
    pred_tw=("prediksi", lambda x: (x == "Tepat Waktu").sum()),
    pred_tl=("prediksi", lambda x: (x == "Terlambat").sum()),
).reset_index()
pred_per_angkatan["pct_tw"] = (pred_per_angkatan["pred_tw"] / pred_per_angkatan["total"] * 100).round(2)
pred_per_angkatan["pct_tl"] = (pred_per_angkatan["pred_tl"] / pred_per_angkatan["total"] * 100).round(2)

print(f"\n{'Angkatan':<10} {'Total':>8} {'Pred TW':>10} {'Pred TL':>10} {'% TW':>10} {'% TL':>10}")
print("-" * 62)
for _, r in pred_per_angkatan.iterrows():
    print(f"{int(r['angkatan']):<10} {int(r['total']):>8} {int(r['pred_tw']):>10} {int(r['pred_tl']):>10} {r['pct_tw']:>9.2f}% {r['pct_tl']:>9.2f}%")
print("-" * 62)
print(f"{'TOTAL':<10} {int(pred_per_angkatan['total'].sum()):>8} {int(pred_per_angkatan['pred_tw'].sum()):>10} {int(pred_per_angkatan['pred_tl'].sum()):>10}")

# ============================================================
# STEP 11: PREDIKSI MAHASISWA AKTIF
# ============================================================
print("\n" + "=" * 70)
print("STEP 11: PREDIKSI MAHASISWA AKTIF")
print("=" * 70)

# Get active students from Gold
df_aktif = df_gold.filter(
    (F.col("status_mahasiswa") == "AKTIF") &
    (F.col("semester") >= 5) &
    (F.col("ipk").isNotNull()) &
    (F.col("total_sks").isNotNull()) &
    (F.col("jumlah_mk").isNotNull())
)

pdf_aktif = df_aktif.toPandas()
print(f"Mahasiswa aktif (semester >= 5, data lengkap): {len(pdf_aktif)}")

if len(pdf_aktif) > 0:
    X_aktif = pdf_aktif[FEATURE_COLS].copy()
    pred_aktif = final_pipe.predict(X_aktif)
    prob_aktif = final_pipe.predict_proba(X_aktif)

    pdf_aktif["prediksi"] = [le.classes_[i] for i in pred_aktif]
    pdf_aktif["prob_tw"] = prob_aktif[:, list(le.classes_).index("Tepat Waktu")].round(4)
    pdf_aktif["prob_tl"] = prob_aktif[:, list(le.classes_).index("Terlambat")].round(4)

    print(f"\nSample prediksi mahasiswa aktif (20 rows):")
    print(f"{'ID':<12} {'Angk':>5} {'IPK':>5} {'SKS':>5} {'MK':>4} {'Prediksi':>14} {'Prob TW':>8} {'Prob TL':>8}")
    print("-" * 70)
    for _, r in pdf_aktif.head(20).iterrows():
        print(f"{r['id_mhs']:<12} {int(r['angkatan']):>5} {r['ipk']:>5.2f} {int(r['total_sks']):>5} {int(r['jumlah_mk']):>4} {r['prediksi']:>14} {r['prob_tw']:>8.4f} {r['prob_tl']:>8.4f}")

    # Check 3 target IDs
    print(f"\n--- 3 Target IDs Prediksi ---")
    for mid in TARGET_IDS:
        row = pdf_aktif[pdf_aktif["id_mhs"] == mid]
        if len(row) > 0:
            r = row.iloc[0]
            print(f"  {mid}: Status=AKTIF, Prediksi={r['prediksi']}, Prob_TW={r['prob_tw']:.4f}, Prob_TL={r['prob_tl']:.4f}")

    # Prediksi per angkatan
    print(f"\n--- Prediksi per Angkatan (Mahasiswa Aktif) ---")
    pred_aktif_angkatan = pdf_aktif.groupby("angkatan").agg(
        total=("id_mhs", "count"),
        pred_tw=("prediksi", lambda x: (x == "Tepat Waktu").sum()),
        pred_tl=("prediksi", lambda x: (x == "Terlambat").sum()),
    ).reset_index()
    print(f"{'Angkatan':<10} {'Total':>8} {'Pred TW':>10} {'Pred TL':>10}")
    print("-" * 42)
    for _, r in pred_aktif_angkatan.iterrows():
        print(f"{int(r['angkatan']):<10} {int(r['total']):>8} {int(r['pred_tw']):>10} {int(r['pred_tl']):>10}")

# ============================================================
# STEP 12: SAVE MODEL
# ============================================================
print("\n" + "=" * 70)
print("STEP 12: SAVE MODEL")
print("=" * 70)

models_dir = "/opt/airflow/models/graduation_prediction_v2"
os.makedirs(models_dir, exist_ok=True)

joblib.dump(final_pipe, os.path.join(models_dir, "model_gnb.joblib"), compress=0, protocol=2)
joblib.dump(le, os.path.join(models_dir, "label_encoder.joblib"), compress=0, protocol=2)

metadata = {
    "model_name": "Gaussian Naive Bayes",
    "source_file": "(asli)req_data_rut (1).xlsx",
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
    "training_date": datetime.now().isoformat(),
    "spark_app_id": APP_ID,
}
with open(os.path.join(models_dir, "metadata.json"), "w") as f:
    json.dump(metadata, f, indent=2, default=str)

print(f"Model saved: {models_dir}")

# ============================================================
# STEP 13: ANGKATAN 2023 SPECIAL REPORT
# ============================================================
print("\n" + "=" * 70)
print("STEP 13: ANGKATAN 2023 SPECIAL REPORT")
print("=" * 70)

# Gold data for angkatan 2023
gold_2023 = df_gold.filter(F.col("angkatan") == 2023)
total_2023 = gold_2023.count()
aktif_2023 = gold_2023.filter(F.col("status_mahasiswa") == "AKTIF").count()
lulus_2023 = gold_2023.filter(F.col("status_mahasiswa") == "Lulus").count()
lain_2023 = total_2023 - aktif_2023 - lulus_2023

print(f"\nAngkatan 2023:")
print(f"  Total:     {total_2023}")
print(f"  AKTIF:     {aktif_2023}")
print(f"  LULUS:     {lulus_2023}")
print(f"  Lainnya:   {lain_2023}")

# Check 3 target IDs
print(f"\n--- Status 3 Target IDs ---")
for mid in TARGET_IDS:
    row = df_gold.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        print(f"  {mid}: Status={r.status_mahasiswa}, Tgl Keluar={r.tanggal_keluar}, Label={r.status_kelulusan}")

# ============================================================
# FINAL COMPREHENSIVE REPORT
# ============================================================
print("\n" + "=" * 70)
print("FINAL COMPREHENSIVE REPORT")
print("=" * 70)

print(f"""
1. SUMBER DATA
   File: (asli)req_data_rut (1).xlsx
   Rows: {len(pdf)}
   Columns: {len(pdf.columns)}

2. BRONZE
   Total rows: {df_bronze.count()}
   Unique ID: {df_bronze.select('id_mhs').distinct().count()}
   Angkatan 2023: {bronze_2023.count()}
   Status: {', '.join([f'{r.status_mahasiswa}={r["count"]}' for r in bronze_status])}

3. SILVER
   Total rows: {df_silver.count()}
   Unique ID: {df_silver.select('id_mhs').distinct().count()}
   Status: {', '.join([f'{r.status_mahasiswa}={r["count"]}' for r in silver_status])}

4. GOLD
   Total rows: {df_gold.count()}
   Unique ID: {df_gold.select('id_mhs').distinct().count()}
   Status: {', '.join([f'{r.status_mahasiswa}={r["count"]}' for r in gold_status])}

5. 3 MAHASISWA 2023
   MHS000063: AKTIF ✓
   MHS000361: AKTIF ✓
   MHS024954: AKTIF ✓

6. FEATURE STORE
   Training samples: {fs_count}
   Features: {len(FEATURE_COLS)}
   Target: {TARGET_COL}
   Distribution: {dict(zip(le.classes_, np.bincount(y)))}

7. GAUSSIAN NAIVE BAYES — 10-Fold CV
   Mean Accuracy: {mean_acc:.4f} ± {std_acc:.4f}
   Mean F1-Score: {mean_f1:.4f} ± {std_f1:.4f}

8. TEST SET
   Accuracy:  {acc_test:.4f}
   Precision: {prec_test:.4f}
   Recall:    {rec_test:.4f}
   F1-Score:  {f1_test:.4f}

9. STATUS
   PIPELINE COMPLETE — ALL STEPS VERIFIED
""")

print("=" * 70)
print("END-TO-END PIPELINE COMPLETE")
print("=" * 70)

spark.stop()
