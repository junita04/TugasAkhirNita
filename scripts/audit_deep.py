"""STEP 5: Deep Audit — Old Data, Snapshots, Caches"""
import warnings
warnings.filterwarnings("ignore")
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

TARGET_IDS = ["MHS000063", "MHS000361", "MHS024954"]

spark = (
    SparkSession.builder
    .appName("TA_Audit_Deep")
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

# ============================================================
# 1. CHECK ALL NAMESPACES/CATALOGS
# ============================================================
print("=" * 70)
print("1. ALL NAMESPACES")
print("=" * 70)
for ns in spark.sql("SHOW NAMESPACES IN iceberg").collect():
    print(f"  {ns[0]}")
    tables = spark.sql(f"SHOW TABLES IN iceberg.{ns[0]}").collect()
    for t in tables:
        print(f"    - {t[1]}")

# ============================================================
# 2. CHECK TABLE SNAPSHOTS
# ============================================================
print("\n" + "=" * 70)
print("2. ICEBERG SNAPSHOTS")
print("=" * 70)

for layer in ["bronze", "silver", "gold", "feature_store"]:
    try:
        snaps = spark.sql(f"SELECT * FROM iceberg.{layer}.data_referensi_mahasiswa.history ORDER BY made_current_at DESC LIMIT 5").collect() if layer != "feature_store" else spark.sql(f"SELECT * FROM iceberg.{layer}.feature_store_graduation_prediction.history ORDER BY made_current_at DESC LIMIT 5").collect()
        print(f"\n{layer}: {len(snaps)} snapshots")
        for s in snaps:
            print(f"  version={s.version_number}, made_at={s.made_current_at}, snapshot_id={s.snapshot_id}")
    except Exception as e:
        print(f"\n{layer}: Error - {e}")

# ============================================================
# 3. CHECK FOR OLD TABLES IN OTHER LOCATIONS
# ============================================================
print("\n" + "=" * 70)
print("3. CHECK OLD TABLE LOCATIONS")
print("=" * 70)

for layer in ["bronze", "silver", "gold", "feature_store"]:
    try:
        loc = spark.sql(f"SHOW CREATE TABLE iceberg.{layer}.data_referensi_mahasiswa").collect() if layer != "feature_store" else spark.sql(f"SHOW CREATE TABLE iceberg.{layer}.feature_store_graduation_prediction").collect()
        for row in loc:
            if "LOCATION" in str(row[0]).upper():
                print(f"  {layer}: {row[0]}")
    except Exception as e:
        print(f"  {layer}: Error - {e}")

# ============================================================
# 4. CHECK OLD EXCEL FILE — COMPARE
# ============================================================
print("\n" + "=" * 70)
print("4. OLD EXCEL FILE vs CURRENT EXCEL")
print("=" * 70)

import pandas as pd

old_file = "/tmp/(asli)req_data_rut (baru).xlsx"
new_file = "/tmp/new_data.xlsx"

try:
    df_old = pd.read_excel(old_file, sheet_name="Referensi Data Mahasiswa", dtype=str)
    df_new = pd.read_excel(new_file, sheet_name="Referensi Data Mahasiswa", dtype=str)
    
    df_old.columns = [c.strip().replace(" ", "_").replace("-", "_").lower() for c in df_old.columns]
    df_new.columns = [c.strip().replace(" ", "_").replace("-", "_").lower() for c in df_new.columns]
    
    print(f"Old Excel rows: {len(df_old)}")
    print(f"New Excel rows: {len(df_new)}")
    
    # Check target IDs in old file
    print("\nOld Excel — Target IDs:")
    for mid in TARGET_IDS:
        row = df_old[df_old["id_mhs"] == mid]
        if len(row) > 0:
            r = row.iloc[0]
            print(f"  {mid}: status={r['status_mahasiswa']}, tgl_keluar={r['tanggal_keluar']}")
        else:
            print(f"  {mid}: NOT FOUND in old Excel!")
    
    print("\nNew Excel — Target IDs:")
    for mid in TARGET_IDS:
        row = df_new[df_new["id_mhs"] == mid]
        if len(row) > 0:
            r = row.iloc[0]
            print(f"  {mid}: status={r['status_mahasiswa']}, tgl_keluar={r['tanggal_keluar']}")
        else:
            print(f"  {mid}: NOT FOUND in new Excel!")
    
    # Compare status distributions
    print("\nOld Excel status distribution:")
    for s, c in df_old["status_mahasiswa"].value_counts().items():
        print(f"  {s}: {c}")
    
    print("\nNew Excel status distribution:")
    for s, c in df_new["status_mahasiswa"].value_counts().items():
        print(f"  {s}: {c}")
    
    # Compare target IDs specifically
    print("\nDifference in target IDs:")
    for mid in TARGET_IDS:
        old_row = df_old[df_old["id_mhs"] == mid]
        new_row = df_new[df_new["id_mhs"] == mid]
        if len(old_row) > 0 and len(new_row) > 0:
            old_status = old_row.iloc[0]["status_mahasiswa"]
            new_status = new_row.iloc[0]["status_mahasiswa"]
            old_tgl = old_row.iloc[0]["tanggal_keluar"]
            new_tgl = new_row.iloc[0]["tanggal_keluar"]
            if old_status != new_status or str(old_tgl) != str(new_tgl):
                print(f"  {mid}: OLD=({old_status}, {old_tgl}) -> NEW=({new_status}, {new_tgl})")
            else:
                print(f"  {mid}: SAME in both files")
except Exception as e:
    print(f"Error: {e}")

# ============================================================
# 5. CHECK BACKEND CODE
# ============================================================
print("\n" + "=" * 70)
print("5. CHECK IF OLD PIPELINE CODE EXISTS")
print("=" * 70)

import os
backend_paths = [
    "/opt/airflow/backend/bronze/bronze.py",
    "/opt/airflow/backend/silver/silver.py",
    "/opt/airflow/backend/gold/gold.py",
    "/opt/airflow/backend/pipeline/pipeline.py",
    "/opt/airflow/backend/prediction/prediction.py",
]
for p in backend_paths:
    if os.path.exists(p):
        print(f"  EXISTS: {p}")
    else:
        print(f"  NOT FOUND: {p}")

# Check scripts directory
scripts_dir = "/opt/airflow/scripts"
if os.path.exists(scripts_dir):
    print(f"\nScripts in {scripts_dir}:")
    for f in os.listdir(scripts_dir):
        print(f"  {f}")

spark.stop()
print("\nDEEP AUDIT COMPLETE")
