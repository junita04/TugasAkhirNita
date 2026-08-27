"""
EXPORT DATASET — Documentation for Thesis Pipeline
====================================================
Exports all datasets used in the pipeline to Excel files.

Pipeline: SIAKAD -> Bronze -> Silver -> Gold -> Feature Store -> Training -> Inference -> Trino -> Superset

Files produced:
  data/00_dataset_summary.xlsx
  data/01_silver_dataset.xlsx
  data/02_gold_dataset.xlsx
  data/03_feature_store.xlsx
  data/04_training_testing.xlsx
  data/05_inference_data.xlsx
  data/06_inference_result.xlsx
"""
import sys, os

sys.path.insert(0, "/opt/airflow")

from pathlib import Path
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import pandas as pd

# ============================================================
# CONFIG
# ============================================================
DATA_DIR = Path("/opt/airflow/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

EXCEL_MAX_ROWS = 1_048_576

# ============================================================
# SPARK INIT
# ============================================================
print("=" * 60)
print("INITIALIZING SPARK")
print("=" * 60)

spark = (
    SparkSession.builder
    .appName("TA_Export_Datasets")
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
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")
print(f"Spark App: {spark.sparkContext.applicationId}")

# ============================================================
# HELPER
# ============================================================
summary_rows = []

def export_to_excel(df_pd, filepath, sheet_name, tahap, nama_dataset):
    """Export pandas DataFrame to Excel, splitting if needed."""
    total_rows = len(df_pd)
    total_cols = len(df_pd.columns)

    if total_rows <= EXCEL_MAX_ROWS:
        df_pd.to_excel(filepath, sheet_name=sheet_name, index=False, engine="openpyxl")
        summary_rows.append({
            "tahap": tahap,
            "nama_dataset": nama_dataset,
            "jumlah_baris": total_rows,
            "jumlah_kolom": total_cols,
            "nama_file": filepath.name,
            "nama_sheet": sheet_name,
        })
        print(f"  [OK] {sheet_name}: {total_rows} rows, {total_cols} cols -> {filepath.name}")
    else:
        chunks = []
        chunk_idx = 1
        for start in range(0, total_rows, EXCEL_MAX_ROWS):
            chunk = df_pd.iloc[start:start + EXCEL_MAX_ROWS]
            chunks.append(chunk)
            chunk_sheet = f"{sheet_name}_{chunk_idx}"
            chunk_file = DATA_DIR / f"{filepath.stem}_{chunk_idx}.xlsx"
            chunk.to_excel(chunk_file, sheet_name=chunk_sheet, index=False, engine="openpyxl")
            summary_rows.append({
                "tahap": tahap,
                "nama_dataset": f"{nama_dataset} (part {chunk_idx})",
                "jumlah_baris": len(chunk),
                "jumlah_kolom": total_cols,
                "nama_file": chunk_file.name,
                "nama_sheet": chunk_sheet,
            })
            print(f"  [OK] {chunk_sheet}: {len(chunk)} rows, {total_cols} cols -> {chunk_file.name}")
            chunk_idx += 1

def read_iceberg(table_name):
    """Read Iceberg table and return Spark DataFrame."""
    print(f"  Reading {table_name}...")
    df = spark.table(table_name)
    count = df.count()
    print(f"  Rows: {count}, Cols: {len(df.columns)}")
    return df

def spark_to_pandas(df_spark):
    """Convert Spark DataFrame to pandas."""
    return df_spark.toPandas()

# ============================================================
# 1. SILVER LAYER
# ============================================================
print("\n" + "=" * 60)
print("1. EXPORTING SILVER LAYER")
print("=" * 60)

df_silver = read_iceberg("iceberg.silver.data_referensi_mahasiswa")
pdf_silver = spark_to_pandas(df_silver)

silver_file = DATA_DIR / "01_silver_dataset.xlsx"
export_to_excel(pdf_silver, silver_file, "silver_data_referensi_mahasiswa", "Silver", "silver_data_referensi_mahasiswa")

# ============================================================
# 2. GOLD LAYER
# ============================================================
print("\n" + "=" * 60)
print("2. EXPORTING GOLD LAYER")
print("=" * 60)

df_gold = read_iceberg("iceberg.gold.data_referensi_mahasiswa")
pdf_gold = spark_to_pandas(df_gold)

gold_file = DATA_DIR / "02_gold_dataset.xlsx"
export_to_excel(pdf_gold, gold_file, "gold_data_referensi_mahasiswa", "Gold", "gold_data_referensi_mahasiswa")

# ============================================================
# 3. FEATURE STORE
# ============================================================
print("\n" + "=" * 60)
print("3. EXPORTING FEATURE STORE")
print("=" * 60)

df_fs = read_iceberg("iceberg.feature_store.feature_store_graduation_prediction")
pdf_fs = spark_to_pandas(df_fs)

fs_file = DATA_DIR / "03_feature_store.xlsx"
export_to_excel(pdf_fs, fs_file, "feature_store", "Feature Store", "feature_store_graduation_prediction")

# ============================================================
# 4. TRAINING + TESTING DATA
#    Rebuild from pipeline logic to ensure consistency
# ============================================================
print("\n" + "=" * 60)
print("4. EXPORTING TRAINING + TESTING DATA")
print("=" * 60)

# Read Gold + KHS (same logic as modeling_pipeline_v2.py)
df_gold_full = read_iceberg("iceberg.gold.data_referensi_mahasiswa")

# Read KHS
df_khs = read_iceberg("iceberg.bronze.data_khs")
df_khs = df_khs.withColumn("ip", F.col("ip").cast("double"))
df_khs = df_khs.withColumn("sks", F.col("sks").cast("int"))

# KHS aggregated
df_khs_agg = df_khs.groupBy("id_mhs").agg(
    F.max("ip").alias("ip"),
    F.max("sks").alias("sks_khs")
)

# Join and build training data
df_gold_with_khs = df_gold_full.join(df_khs_agg, on="id_mhs", how="left")
df_gold_final = df_gold_with_khs.withColumn("sks_seharusnya", F.col("target_sks_kumulatif"))

# Training: Lulus only
df_lulus = df_gold_final.filter(
    (F.col("status_mahasiswa") == "Lulus") &
    (F.col("ip").isNotNull()) &
    (F.col("lama_studi").isNotNull())
)

# Label
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

FEATURE_COLS = [
    "jenis_kelamin", "angkatan", "ip", "ipk", "total_sks",
    "jumlah_mk", "sks_seharusnya", "selisih_sks",
]

# Convert to pandas
pdf_train_full = df_labeled.select("id_mhs", *FEATURE_COLS, "label").toPandas()

# Encode jenis_kelamin
pdf_train_full["jenis_kelamin"] = (
    pdf_train_full["jenis_kelamin"]
    .astype(str).str.strip().str.upper()
    .map({"P": 0, "L": 1})
)

# Train/test split (same params as pipeline)
from sklearn.model_selection import train_test_split
import numpy as np

X_all = pdf_train_full[FEATURE_COLS].copy()
y_raw = pdf_train_full["label"].copy()
le_map = {"Tepat Waktu": 0, "Terlambat": 1}
y_all = y_raw.map(le_map).values

X_train, X_test, y_train, y_test = train_test_split(
    X_all, y_all, test_size=0.20, stratify=y_all, random_state=42
)

# Build training DataFrame
pdf_train = pdf_train_full.iloc[X_train.index].copy()
pdf_train["dataset_type"] = "train"
pdf_train["label_encoded"] = y_train

# Build testing DataFrame
pdf_test = pdf_train_full.iloc[X_test.index].copy()
pdf_test["dataset_type"] = "test"
pdf_test["label_encoded"] = y_test

train_test_file = DATA_DIR / "04_training_testing.xlsx"

with pd.ExcelWriter(train_test_file, engine="openpyxl") as writer:
    pdf_train.to_excel(writer, sheet_name="training_data", index=False)
    pdf_test.to_excel(writer, sheet_name="testing_data", index=False)

summary_rows.append({
    "tahap": "Training",
    "nama_dataset": "training_data",
    "jumlah_baris": len(pdf_train),
    "jumlah_kolom": len(pdf_train.columns),
    "nama_file": train_test_file.name,
    "nama_sheet": "training_data",
})
summary_rows.append({
    "tahap": "Testing",
    "nama_dataset": "testing_data",
    "jumlah_baris": len(pdf_test),
    "jumlah_kolom": len(pdf_test.columns),
    "nama_file": train_test_file.name,
    "nama_sheet": "testing_data",
})
print(f"  [OK] training_data: {len(pdf_train)} rows, {len(pdf_train.columns)} cols")
print(f"  [OK] testing_data: {len(pdf_test)} rows, {len(pdf_test.columns)} cols")

# ============================================================
# 5. INFERENCE DATA
# ============================================================
print("\n" + "=" * 60)
print("5. EXPORTING INFERENCE DATA")
print("=" * 60)

df_aktif = df_gold_final.filter(
    (F.col("status_mahasiswa") == "AKTIF") &
    (F.col("ip").isNotNull()) &
    (F.col("ipk").isNotNull()) &
    (F.col("total_sks").isNotNull()) &
    (F.col("jumlah_mk").isNotNull()) &
    (F.col("sks_seharusnya").isNotNull()) &
    (F.col("selisih_sks").isNotNull())
)

pdf_inf = df_aktif.select("id_mhs", *FEATURE_COLS).toPandas()
pdf_inf["jenis_kelamin"] = (
    pdf_inf["jenis_kelamin"]
    .astype(str).str.strip().str.upper()
    .map({"P": 0, "L": 1})
)

inf_file = DATA_DIR / "05_inference_data.xlsx"
export_to_excel(pdf_inf, inf_file, "inference_data", "Inference", "inference_data")

# ============================================================
# 6. INFERENCE RESULT
# ============================================================
print("\n" + "=" * 60)
print("6. EXPORTING INFERENCE RESULT")
print("=" * 60)

import joblib

model_path = "/opt/airflow/models/graduation_prediction_final/gaussian_nb_final.joblib"
final_pipe = joblib.load(model_path)

X_inf = pdf_inf[FEATURE_COLS].copy()
pred = final_pipe.predict(X_inf)
prob = final_pipe.predict_proba(X_inf)

pdf_result = pdf_inf.copy()
pdf_result["prediksi"] = ["Tepat Waktu" if i == 0 else "Terlambat" for i in pred]
pdf_result["prob_tepat_waktu"] = prob[:, 0].round(4)
pdf_result["prob_terlambat"] = prob[:, 1].round(4)
pdf_result["jenis_kelamin"] = pdf_result["jenis_kelamin"].map({0: "P", 1: "L"})

result_file = DATA_DIR / "06_inference_result.xlsx"
export_to_excel(pdf_result, result_file, "inference_result", "Inference", "inference_result")

# ============================================================
# 7. DATASET SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("7. CREATING DATASET SUMMARY")
print("=" * 60)

pdf_summary = pd.DataFrame(summary_rows)
summary_file = DATA_DIR / "00_dataset_summary.xlsx"
pdf_summary.to_excel(summary_file, sheet_name="summary", index=False, engine="openpyxl")
print(f"  [OK] summary: {len(pdf_summary)} rows -> {summary_file.name}")

# ============================================================
# FINAL REPORT
# ============================================================
print("\n" + "=" * 60)
print("DATASET EXPORT SUMMARY")
print("=" * 60)

for _, row in pdf_summary.iterrows():
    print(f"  [{row['tahap']:15s}] {row['nama_dataset']:40s} | {row['jumlah_baris']:>8} rows | {row['jumlah_kolom']:>3} cols | {row['nama_file']}")

print(f"\n{'=' * 60}")
print(f"ALL DATASET EXPORT COMPLETED")
print(f"Files saved to: {DATA_DIR}")
print(f"{'=' * 60}")

# List files
print("\nFiles:")
for f in sorted(DATA_DIR.glob("*.xlsx")):
    size = f.stat().st_size
    print(f"  {f.name:40s} {size:>10} bytes")

spark.stop()
print("\nEXPORT COMPLETE")
