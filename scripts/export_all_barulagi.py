"""
Export Pipeline Data to Excel (_barulagi)
==========================================
Reads all layers from Iceberg and saves to Excel files in data/ folder.
Uses the exact same logic and tables as the existing pipeline.
"""
import sys, time, gc
sys.path.insert(0, '/opt/airflow')

import pandas as pd
import numpy as np
from pathlib import Path
from backend.spark.session import get_spark
from backend.config.settings import ICEBERG_NAMESPACE

DATA_DIR = Path('/opt/airflow/data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

SUFFIX = "_barulagi"

# ============================================================
# Helper: Spark table -> pandas -> Excel
# ============================================================
def spark_to_excel(spark, iceberg_table, excel_path, label=None):
    """Read an Iceberg table, convert to pandas, save as Excel."""
    name = label or iceberg_table.split(".")[-1]
    print(f"  Reading {iceberg_table} ...", end=" ", flush=True)
    df = spark.table(iceberg_table)
    count = df.count()
    print(f"{count} rows", end=" ", flush=True)
    pandas_df = df.toPandas()
    pandas_df.to_excel(excel_path, index=False, engine='openpyxl')
    print(f"-> {excel_path.name}")
    return count, len(pandas_df.columns)

# ============================================================
# STEP 1: BRONZE
# ============================================================
print("=" * 80)
print("STEP 1: BRONZE LAYER")
print("=" * 80)

spark = get_spark("Export Barulagi - Bronze")

bronze_tables = {
    "data_referensi_mahasiswa": f"{ICEBERG_NAMESPACE}.bronze.data_referensi_mahasiswa",
    "data_khs": f"{ICEBERG_NAMESPACE}.bronze.data_khs",
    "data_program_studi": f"{ICEBERG_NAMESPACE}.bronze.data_program_studi",
    "data_kelas": f"{ICEBERG_NAMESPACE}.bronze.data_kelas",
    "data_kurikulum": f"{ICEBERG_NAMESPACE}.bronze.data_kurikulum",
}

bronze_stats = {}
for name, table in bronze_tables.items():
    try:
        count, cols = spark_to_excel(spark, table, DATA_DIR / f"bronze_{name}{SUFFIX}.xlsx", name)
        bronze_stats[name] = {"rows": count, "cols": cols}
    except Exception as e:
        print(f"  ERROR {name}: {e}")
        bronze_stats[name] = {"rows": 0, "cols": 0, "error": str(e)}

spark.stop()
gc.collect()
time.sleep(2)

# ============================================================
# STEP 2: SILVER
# ============================================================
print()
print("=" * 80)
print("STEP 2: SILVER LAYER")
print("=" * 80)

spark = get_spark("Export Barulagi - Silver")

silver_tables = {
    "silver_mahasiswa": f"{ICEBERG_NAMESPACE}.silver.silver_mahasiswa",
    "silver_khs": f"{ICEBERG_NAMESPACE}.silver.silver_khs",
    "silver_program_studi": f"{ICEBERG_NAMESPACE}.silver.silver_program_studi",
    "silver_kelas": f"{ICEBERG_NAMESPACE}.silver.silver_kelas",
    "silver_kurikulum": f"{ICEBERG_NAMESPACE}.silver.silver_kurikulum",
}

silver_stats = {}
for name, table in silver_tables.items():
    try:
        count, cols = spark_to_excel(spark, table, DATA_DIR / f"silver_{name}{SUFFIX}.xlsx", name)
        silver_stats[name] = {"rows": count, "cols": cols}
    except Exception as e:
        print(f"  ERROR {name}: {e}")
        silver_stats[name] = {"rows": 0, "cols": 0, "error": str(e)}

spark.stop()
gc.collect()
time.sleep(2)

# ============================================================
# STEP 3: GOLD
# ============================================================
print()
print("=" * 80)
print("STEP 3: GOLD LAYER")
print("=" * 80)

spark = get_spark("Export Barulagi - Gold")

gold_tables = {
    "dim_mahasiswa": f"{ICEBERG_NAMESPACE}.gold.dim_mahasiswa",
    "fact_khs": f"{ICEBERG_NAMESPACE}.gold.fact_khs",
}

gold_stats = {}
for name, table in gold_tables.items():
    try:
        count, cols = spark_to_excel(spark, table, DATA_DIR / f"gold_{name}{SUFFIX}.xlsx", name)
        gold_stats[name] = {"rows": count, "cols": cols}
    except Exception as e:
        print(f"  ERROR {name}: {e}")
        gold_stats[name] = {"rows": 0, "cols": 0, "error": str(e)}

# Also export Gold ML tables (for Superset)
gold_ml_tables = {
    "model_metrics_final": f"{ICEBERG_NAMESPACE}.gold.model_metrics_final",
    "confusion_matrix_final": f"{ICEBERG_NAMESPACE}.gold.confusion_matrix_final",
    "classification_report_final": f"{ICEBERG_NAMESPACE}.gold.classification_report_final",
    "prediction_by_angkatan_final": f"{ICEBERG_NAMESPACE}.gold.prediction_by_angkatan_final",
    "model_predictions": f"{ICEBERG_NAMESPACE}.gold.model_predictions",
}

for name, table in gold_ml_tables.items():
    try:
        count, cols = spark_to_excel(spark, table, DATA_DIR / f"gold_{name}{SUFFIX}.xlsx", name)
        gold_stats[name] = {"rows": count, "cols": cols}
    except Exception as e:
        print(f"  WARNING {name}: {e}")

spark.stop()
gc.collect()
time.sleep(2)

# ============================================================
# STEP 4: FEATURE STORE
# ============================================================
print()
print("=" * 80)
print("STEP 4: FEATURE STORE")
print("=" * 80)

spark = get_spark("Export Barulagi - Feature Store")

# Read from Iceberg feature_store tables
FEATURE_X = ["jk_enc","angkatan","ip","ipk","total_sks","jumlah_mk","sks_seharusnya","selisih_sks"]

# Training dataset from Iceberg (already has IP NULL filtered, deduplicated)
print("  Reading training_dataset ...", end=" ", flush=True)
training_df = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.training_dataset")
train_count = training_df.count()
print(f"{train_count} rows", end=" ", flush=True)
train_pandas = training_df.toPandas()
train_pandas.to_excel(DATA_DIR / f"feature_store_training{SUFFIX}.xlsx", index=False, engine='openpyxl')
print(f"-> feature_store_training{SUFFIX}.xlsx")

# Inference dataset from Iceberg
print("  Reading inference_dataset ...", end=" ", flush=True)
inference_df = spark.table(f"{ICEBERG_NAMESPACE}.feature_store.inference_dataset")
inf_count = inference_df.count()
print(f"{inf_count} rows", end=" ", flush=True)
inf_pandas = inference_df.toPandas()
inf_pandas.to_excel(DATA_DIR / f"feature_store_inference{SUFFIX}.xlsx", index=False, engine='openpyxl')
print(f"-> feature_store_inference{SUFFIX}.xlsx")

spark.stop()
gc.collect()
time.sleep(2)

# ============================================================
# STEP 5: TRAINING DATASET (8 features + label)
# ============================================================
print()
print("=" * 80)
print("STEP 5: TRAINING DATASET (8 features)")
print("=" * 80)

# train_pandas already loaded above - select only the 8 features + label + id
train_features = train_pandas[["id_mahasiswa"] + FEATURE_X + ["label"]].copy()
train_features.to_excel(DATA_DIR / f"training_8_features{SUFFIX}.xlsx", index=False, engine='openpyxl')
print(f"  Saved: training_8_features{SUFFIX}.xlsx ({len(train_features)} rows, {len(train_features.columns)} cols)")
print(f"  Features: {FEATURE_X}")
print(f"  Label distribution: {dict(train_features['label'].value_counts())}")

# ============================================================
# STEP 6: INFERENCE DATASET (8 features only)
# ============================================================
print()
print("=" * 80)
print("STEP 6: INFERENCE DATASET (8 features)")
print("=" * 80)

# inf_pandas already loaded above
inf_features = inf_pandas[["id_mahasiswa"] + FEATURE_X].copy()
inf_features.to_excel(DATA_DIR / f"inference_2022_2024{SUFFIX}.xlsx", index=False, engine='openpyxl')
print(f"  Saved: inference_2022_2024{SUFFIX}.xlsx ({len(inf_features)} rows, {len(inf_features.columns)} cols)")
print(f"  Angkatan distribution: {dict(inf_features['angkatan'].value_counts().sort_index())}")

# ============================================================
# SUMMARY
# ============================================================
print()
print("=" * 80)
print("HASIL EXPORT DATA _BARULAGI")
print("=" * 80)

print()
print("BRONZE")
for name, stat in bronze_stats.items():
    print(f"  bronze_{name}{SUFFIX}.xlsx : {stat['rows']} rows, {stat['cols']} cols")

print()
print("SILVER")
for name, stat in silver_stats.items():
    print(f"  silver_{name}{SUFFIX}.xlsx : {stat['rows']} rows, {stat['cols']} cols")

print()
print("GOLD")
for name, stat in gold_stats.items():
    print(f"  gold_{name}{SUFFIX}.xlsx : {stat['rows']} rows, {stat['cols']} cols")

print()
print("FEATURE STORE")
print(f"  feature_store_training{SUFFIX}.xlsx : {train_count} rows")
print(f"  feature_store_inference{SUFFIX}.xlsx : {inf_count} rows")

print()
print("TRAINING")
print(f"  training_8_features{SUFFIX}.xlsx : {len(train_features)} rows, {len(train_features.columns)} cols")
print(f"  Features: {FEATURE_X}")
print(f"  Label dist: {dict(train_features['label'].value_counts())}")

print()
print("INFERENCE")
print(f"  inference_2022_2024{SUFFIX}.xlsx : {len(inf_features)} rows, {len(inf_features.columns)} cols")
print(f"  Angkatan dist: {dict(inf_features['angkatan'].value_counts().sort_index())}")

# List all files
print()
print("FILES CREATED:")
for f in sorted(DATA_DIR.glob(f"*{SUFFIX}.xlsx")):
    size_kb = f.stat().st_size / 1024
    print(f"  {f.name} ({size_kb:.1f} KB)")

print()
print("EXPORT SELESAI")
