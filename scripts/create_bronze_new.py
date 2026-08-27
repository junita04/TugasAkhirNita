"""
Create new Bronze table from new Excel dataset.
- Reads Excel file
- Normalizes column names to snake_case
- Converts pandas NaN to Python None (SQL NULL in Spark)
- Writes to Iceberg at s3a://warehouse/iceberg/bronze/data_referensi_mahasiswa
- Does NOT modify data values, only column names and missing value representation
"""
import sys
import os

sys.path.insert(0, "/opt/airflow")

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import re

def normalize_column_name(column_name: str) -> str:
    """Convert Excel column name to snake_case."""
    if not isinstance(column_name, str):
        return str(column_name)
    
    # Strip whitespace
    name = column_name.strip()
    
    # Replace spaces with underscore
    name = name.replace(" ", "_")
    
    # Replace hyphens with underscore
    name = name.replace("-", "_")
    
    # Remove special characters
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    
    # Convert to lowercase
    name = name.lower()
    
    # Handle multiple underscores
    name = re.sub(r"_+", "_", name)
    
    # Remove leading/trailing underscores
    name = name.strip("_")
    
    return name

# ============================================================
# Initialize Spark with Iceberg
# ============================================================
print("=" * 60)
print("INITIALIZING SPARK WITH ICEBERG")
print("=" * 60)

spark = (
    SparkSession.builder
    .appName("TA_Bronze_Create_Data_Referensi_Mahasiswa")
    .master("local[*]")
    .config("spark.driver.extraClassPath", "/opt/airflow/jars/*")
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin-password")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    # Handle s3:// scheme (for old metadata)
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

print("Spark session created")
print(f"Application ID: {spark.sparkContext.applicationId}")
print(f"Application Name: {spark.sparkContext.appName}")

# ============================================================
# Read Excel file
# ============================================================
print("=" * 60)
print("READING EXCEL FILE")
print("=" * 60)

import pandas as pd
print("Reading Excel with pandas...")
pdf = pd.read_excel("/tmp/(asli)req_data_rut (baru).xlsx", 
                    sheet_name="Referensi Data Mahasiswa",
                    dtype=str)  # Read all as string to preserve original values

print(f"Pandas shape: {pdf.shape}")
print(f"Original columns: {list(pdf.columns)}")

# Normalize column names
new_columns = [normalize_column_name(c) for c in pdf.columns]
print(f"Normalized columns: {new_columns}")

pdf.columns = new_columns

# ============================================================
# CRITICAL FIX: Convert pandas NaN -> Python None -> Spark SQL NULL
# ============================================================
print("=" * 60)
print("CONVERTING PANDAS NaN TO PYTHON NONE")
print("=" * 60)

# Count NaN before conversion
nan_before = pdf.isna().sum()
print(f"NaN counts before conversion:")
for col in pdf.columns:
    print(f"  {col}: {nan_before[col]}")

# Convert all NaN/NaT to None (Python None -> Spark SQL NULL)
pdf = pdf.where(pd.notna(pdf), None)

# Count NaN after conversion
nan_after = pdf.isna().sum()
print(f"NaN counts after conversion:")
for col in pdf.columns:
    print(f"  {col}: {nan_after[col]}")

# ============================================================
# Convert to Spark DataFrame
# ============================================================
print("=" * 60)
print("CONVERTING TO SPARK DATAFRAME")
print("=" * 60)

df = spark.createDataFrame(pdf)
print(f"Spark DataFrame columns: {df.columns}")
print(f"Spark DataFrame count: {df.count()}")

# Show sample
df.show(5, truncate=False)

# ============================================================
# Write to Iceberg
# ============================================================
print("=" * 60)
print("WRITING TO ICEBERG")
print("=" * 60)

table_name = "iceberg.bronze.data_referensi_mahasiswa"

# Drop table if exists (to overwrite with new schema)
spark.sql(f"DROP TABLE IF EXISTS {table_name}")

# Write as Iceberg table
(
    df.writeTo("iceberg.bronze.data_referensi_mahasiswa")
    .using("iceberg")
    .createOrReplace()
)

print(f"Table {table_name} created successfully")

# ============================================================
# Validation
# ============================================================
print("=" * 60)
print("VALIDATION")
print("=" * 60)

df_val = spark.table("iceberg.bronze.data_referensi_mahasiswa")

# 1. Row count
count = df_val.count()
print(f"1. Row count: {count}")

# 2. Column count
col_count = len(df_val.columns)
print(f"2. Column count: {col_count}")
print(f"   Columns: {df_val.columns}")

# 3. NULL tanggal_masuk
null_tanggal_masuk = df_val.filter(F.col("tanggal_masuk").isNull()).count()
print(f"3. NULL tanggal_masuk: {null_tanggal_masuk}")

# 4. String "NaN" on tanggal_masuk
nan_str_tanggal_masuk = df_val.filter(
    F.lower(F.trim(F.col("tanggal_masuk"))) == "nan"
).count()
print(f"4. String 'NaN' tanggal_masuk: {nan_str_tanggal_masuk}")

# 5. String "NaN" on ALL columns
print("5. String 'NaN' check on ALL columns:")
for col_name in df_val.columns:
    nan_cnt = df_val.filter(
        F.lower(F.trim(F.col(col_name))) == "nan"
    ).count()
    if nan_cnt > 0:
        print(f"   WARNING: {col_name} has {nan_cnt} 'NaN' strings")

# 6. Duplicate id_mhs
dup_count = df_val.groupBy("id_mhs").count().filter("count > 1").count()
print(f"6. Duplicate id_mhs: {dup_count}")

# 7. Status mahasiswa distribution
print("7. Status mahasiswa distribution:")
df_val.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).show()

# 8. Schema
print("8. Schema:")
df_val.printSchema()

# 9. Sample data
print("9. Sample data (10 rows):")
df_val.show(10, truncate=False)

# 10. Table location
print("10. Table location:")
location = spark.sql("SHOW CREATE TABLE iceberg.bronze.data_referensi_mahasiswa").collect()
for row in location:
    print(f"    {row[0]}")

spark.stop()
print("=" * 60)
print("CREATE_BRONZE_COMPLETE")
print("=" * 60)
