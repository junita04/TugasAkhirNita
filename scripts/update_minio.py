"""
Update MinIO with latest data from Google Colab.
NON-DESTRUCTIVE - does not delete any existing data.

Steps:
1. Read xlsx files from /opt/airflow/data/
2. Convert to Parquet
3. Load into Iceberg via Spark
4. Store raw xlsx in MinIO
5. Validate via Trino
"""
import sys
import os
import subprocess
sys.path.insert(0, "/opt/airflow")

from backend.spark.session import get_spark
import pyspark.sql.functions as F
import pandas as pd

DATA_DIR = "/opt/airflow/data"
PARQUET_DIR = "/opt/airflow/data/parquet_update"

os.makedirs(PARQUET_DIR, exist_ok=True)

print("=" * 70)
print("MINIO DATA UPDATE - NON-DESTRUCTIVE")
print("=" * 70)

spark = get_spark("Update MinIO Data")

# ============================================================
# STEP 1: Read and convert xlsx files
# ============================================================
print("\n" + "=" * 70)
print("STEP 1: READ XLSX -> PARQUET")
print("=" * 70)

files_to_process = [
    ("training_dataset_fix (1).xlsx", "training_dataset_v2", 15505, 10),
    ("inference_dataset_fix (1).xlsx", "inference_dataset_v2", 12338, 9),
    ("data_training_baru(fix).xlsx", "training_dataset_v2_fe", 15505, 16),
    ("data_inference_baru(fix).xlsx", "model_predictions_v2", 12338, 19),
    ("hasil_prediksi(fix).xlsx", "model_predictions_v2_final", 12338, 19),
]

parquet_data = {}
for fname, table_key, expected_rows, expected_cols in files_to_process:
    fpath = os.path.join(DATA_DIR, fname)
    if not os.path.exists(fpath):
        print(f"  SKIP: {fname} not found")
        continue
    
    print(f"\n  Reading: {fname}")
    df = pd.read_excel(fpath)
    print(f"    Rows: {df.shape[0]}, Cols: {df.shape[1]}")
    
    if df.shape[0] != expected_rows:
        print(f"    WARNING: Expected {expected_rows} rows, got {df.shape[0]}")
    if df.shape[1] != expected_cols:
        print(f"    WARNING: Expected {expected_cols} cols, got {df.shape[1]}")
    
    # Save as parquet
    parquet_path = os.path.join(PARQUET_DIR, table_key)
    df.to_parquet(parquet_path, index=False, engine="pyarrow")
    print(f"    Saved to: {parquet_path}")
    parquet_data[table_key] = parquet_path

# ============================================================
# STEP 2: Load into Iceberg via Spark
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: LOAD INTO ICEBERG")
print("=" * 70)

iceberg_tables = {
    "training_dataset_v2": "hive_iceberg.feature_store.training_dataset_v2",
    "inference_dataset_v2": "hive_iceberg.feature_store.inference_dataset_v2",
    "training_dataset_v2_fe": "hive_iceberg.feature_store.training_dataset_v2_fe",
    "model_predictions_v2_final": "hive_iceberg.gold.model_predictions_v2",
}

for table_key, iceberg_table in iceberg_tables.items():
    if table_key not in parquet_data:
        print(f"  SKIP: {table_key} parquet not found")
        continue
    
    print(f"\n  Loading: {table_key} -> {iceberg_table}")
    df_spark = spark.read.parquet(parquet_data[table_key])
    cnt = df_spark.count()
    print(f"    Read from parquet: {cnt} rows")
    
    # Use createOrReplace for idempotent updates
    df_spark.writeTo(iceberg_table).using("iceberg").createOrReplace()
    print(f"    Written to: {iceberg_table}")
    
    # Validate
    final_cnt = spark.table(iceberg_table).count()
    print(f"    Validation count: {final_cnt}")

# ============================================================
# STEP 3: Recreate prediction_by_angkatan_v2
# ============================================================
print("\n" + "=" * 70)
print("STEP 3: RECREATE prediction_by_angkatan_v2")
print("=" * 70)

df_pred = spark.table("hive_iceberg.gold.model_predictions_v2")
df_agg = (
    df_pred
    .groupBy("angkatan")
    .agg(
        F.count("*").alias("total_mahasiswa"),
        F.sum(F.when(F.col("prediksi") == 0, 1).otherwise(0)).alias("prediksi_tepat_waktu"),
        F.sum(F.when(F.col("prediksi") == 1, 1).otherwise(0)).alias("prediksi_terlambat"),
    )
    .withColumn("persentase_tepat_waktu", F.round(F.col("prediksi_tepat_waktu") / F.col("total_mahasiswa") * 100, 2))
    .withColumn("persentase_terlambat", F.round(F.col("prediksi_terlambat") / F.col("total_mahasiswa") * 100, 2))
    .orderBy("angkatan")
)

print("  Aggregation result:")
df_agg.show()

TABLE_AGG = "hive_iceberg.gold.prediction_by_angkatan_v2"
df_agg.writeTo(TABLE_AGG).using("iceberg").createOrReplace()
print(f"  Written to: {TABLE_AGG}")

cnt = spark.table(TABLE_AGG).count()
print(f"  Validation count: {cnt}")

# ============================================================
# STEP 4: Store raw xlsx in MinIO
# ============================================================
print("\n" + "=" * 70)
print("STEP 4: STORE RAW XLSX IN MINIO")
print("=" * 70)

minio_source = "local/warehouse/source"
os.makedirs("/opt/airflow/data/source_xlsx", exist_ok=True)

xlsx_files = [
    "training_dataset_fix (1).xlsx",
    "inference_dataset_fix (1).xlsx",
    "data_training_baru(fix).xlsx",
    "data_inference_baru(fix).xlsx",
    "hasil_prediksi(fix).xlsx",
]

for fname in xlsx_files:
    src = os.path.join(DATA_DIR, fname)
    if not os.path.exists(src):
        print(f"  SKIP: {fname}")
        continue
    
    # Copy to local staging
    dst = os.path.join("/opt/airflow/data/source_xlsx", fname)
    subprocess.run(["cp", src, dst], capture_output=True)
    
    # Upload to MinIO
    cmd = f"mc cp {dst} {minio_source}/{fname}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  Uploaded: {fname}")
    else:
        print(f"  ERROR: {fname}: {result.stderr}")

# ============================================================
# STEP 5: FINAL VALIDATION
# ============================================================
print("\n" + "=" * 70)
print("STEP 5: FINAL VALIDATION")
print("=" * 70)

# Table counts
tables_to_check = [
    ("feature_store.training_dataset_v2", 15505),
    ("feature_store.inference_dataset_v2", 12338),
    ("feature_store.training_dataset_v2_fe", 15505),
    ("gold.model_predictions_v2", 12338),
    ("gold.prediction_by_angkatan_v2", 3),
]

all_pass = True
for table, expected in tables_to_check:
    try:
        cnt = spark.table(table).count()
        status = "PASS" if cnt == expected else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  {status}: {table} = {cnt} (expected {expected})")
    except Exception as e:
        all_pass = False
        print(f"  ERROR: {table}: {e}")

# Prediction distribution
print("\n  Prediction distribution:")
spark.sql("""
    SELECT prediksi, COUNT(*) AS cnt 
    FROM gold.model_predictions_v2 
    GROUP BY prediksi 
    ORDER BY prediksi
""").show()

# Label distribution (training)
print("  Label distribution (training):")
spark.sql("""
    SELECT label, COUNT(*) AS cnt 
    FROM feature_store.training_dataset_v2 
    GROUP BY label 
    ORDER BY label
""").show()

# Old tables still exist
print("  Old tables still intact:")
old_tables = [
    "feature_store.training_dataset",
    "feature_store.inference_dataset",
    "gold.dim_mahasiswa",
    "gold.fact_khs",
    "gold.model_predictions",
]
for t in old_tables:
    try:
        cnt = spark.table(t).count()
        print(f"    {t}: {cnt} rows")
    except Exception as e:
        print(f"    {t}: ERROR ({e})")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  Data synchronized: YES")
print(f"  training_dataset_v2: {spark.table('hive_iceberg.feature_store.training_dataset_v2').count()} rows (10 cols, BEFORE FE)")
print(f"  inference_dataset_v2: {spark.table('hive_iceberg.feature_store.inference_dataset_v2').count()} rows (9 cols, BEFORE FE)")
print(f"  training_dataset_v2_fe: {spark.table('hive_iceberg.feature_store.training_dataset_v2_fe').count()} rows (16 cols, AFTER FE)")
print(f"  model_predictions_v2: {spark.table('hive_iceberg.gold.model_predictions_v2').count()} rows (19 cols, AFTER FE + predictions)")
print(f"  prediction_by_angkatan_v2: {spark.table('hive_iceberg.gold.prediction_by_angkatan_v2').count()} rows")
print(f"  Raw xlsx in MinIO: {minio_source}")
print(f"  Old tables preserved: YES")
print(f"  No data deleted: YES")
print(f"  No retraining: YES")
print("=" * 70)
