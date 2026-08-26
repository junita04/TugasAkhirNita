"""
Create new Bronze table from new Excel dataset.
- Reads Excel file
- Normalizes column names to snake_case
- Writes to Iceberg at s3://warehouse/iceberg/bronze/data_referensi_mahasiswa
- Does NOT modify data values, only column names
"""
import sys
import os

sys.path.insert(0, "/opt/airflow")
os.environ["SPARK_EVENT_LOG"] = "false"

from pyspark.sql import SparkSession
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
    .appName("CreateBronzeFromNewExcel")
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
    .getOrCreate()
)

print("Spark session created")

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

# Convert to Spark DataFrame
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

# Count
count = spark.table("iceberg.bronze.data_referensi_mahasiswa").count()
print(f"Row count: {count}")

# Null check on tanggal_masuk
null_count = spark.table("iceberg.bronze.data_referensi_mahasiswa").filter("tanggal_masuk IS NULL").count()
print(f"NULL tanggal_masuk: {null_count}")

# Duplicate check on id_mhs
dup_count = spark.table("iceberg.bronze.data_referensi_mahasiswa").groupBy("id_mhs").count().filter("count > 1").count()
print(f"Duplicate id_mhs: {dup_count}")

# Show schema
spark.table("iceberg.bronze.data_referensi_mahasiswa").printSchema()

# Show 5 rows
spark.table("iceberg.bronze.data_referensi_mahasiswa").show(5, truncate=False)

spark.stop()
print("=" * 60)
print("CREATE_BRONZE_COMPLETE")
print("=" * 60)