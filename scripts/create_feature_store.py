"""
Create Feature Store from Gold layer for graduation prediction ML.

Target: status_kelulusan (Tepat Waktu / Terlambat)
Filter: mahasiswa semester 5+ yang sudah LULUS

Feature Selection (no data leakage):
- jenis_kelamin: demographic, known at enrollment
- ipk: current academic performance
- total_sks: accumulated credits
- jumlah_mk: accumulated courses
- angkatan: enrollment year
- semester: current semester
- target_sks_kumulatif: curriculum target
- selisih_sks: gap between actual and target

Excluded (data leakage):
- status_kelulusan: TARGET/VARIABLE, not feature
- tanggal_keluar: only available after graduation
- lama_studi: only available after graduation
- status_mahasiswa: contains graduation status
"""
import sys
import os

sys.path.insert(0, "/opt/airflow")

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# ============================================================
# Initialize Spark with Iceberg
# ============================================================
print("=" * 60)
print("INITIALIZING SPARK WITH ICEBERG")
print("=" * 60)

spark = (
    SparkSession.builder
    .appName("TA_Feature_Store_Creation")
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

print("Spark session created")
print(f"Application ID: {spark.sparkContext.applicationId}")
print(f"Application Name: {spark.sparkContext.appName}")

# ============================================================
# Read Gold
# ============================================================
print("=" * 60)
print("READING GOLD TABLE")
print("=" * 60)

gold_table = "iceberg.gold.data_referensi_mahasiswa"
df_gold = spark.table(gold_table)

gold_count = df_gold.count()
print(f"Gold table: {gold_table}")
print(f"Gold row count: {gold_count}")
print(f"Gold columns: {df_gold.columns}")
df_gold.printSchema()

# Show distribution before filtering
print("\nGold status_mahasiswa distribution:")
df_gold.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).show()

print("Gold semester distribution:")
df_gold.groupBy("semester").count().orderBy("semester").show()

print("Gold status_kelulusan distribution:")
df_gold.groupBy("status_kelulusan").count().orderBy(F.col("count").desc()).show()

# ============================================================
# Feature Store Creation
# ============================================================
print("=" * 60)
print("FEATURE STORE CREATION")
print("=" * 60)

# Step 1: Filter semester >= 5
print("\nStep 1: Filter semester >= 5")
df_fs = df_gold.filter(F.col("semester") >= 5)
count_sem5 = df_fs.count()
print(f"  Rows after semester filter: {count_sem5}")

# Step 2: Filter status_mahasiswa == Lulus
print("\nStep 2: Filter status_mahasiswa == Lulus")
df_fs = df_fs.filter(F.col("status_mahasiswa") == "Lulus")
count_lulus = df_fs.count()
print(f"  Rows after Lulus filter: {count_lulus}")

# Step 3: Filter status_kelulusan IS NOT NULL
print("\nStep 3: Filter status_kelulusan IS NOT NULL")
df_fs = df_fs.filter(F.col("status_kelulusan").isNotNull())
count_valid = df_fs.count()
print(f"  Rows after valid target filter: {count_valid}")

# Step 4: Select features (NO data leakage)
print("\nStep 4: Select features")
FEATURE_COLUMNS = [
    "id_mhs",           # Primary key
    "jenis_kelamin",    # Feature: demographic
    "ipk",              # Feature: academic performance
    "total_sks",        # Feature: accumulated credits
    "jumlah_mk",        # Feature: accumulated courses
    "angkatan",         # Feature: enrollment year
    "semester",         # Feature: current semester
    "target_sks_kumulatif",  # Feature: curriculum target
    "selisih_sks",      # Feature: gap between actual and target
    "status_kelulusan", # TARGET/LABEL
]

df_fs = df_fs.select(*FEATURE_COLUMNS)
print(f"  Selected columns: {df_fs.columns}")
print(f"  Row count: {df_fs.count()}")

# Step 5: Check for duplicates
print("\nStep 5: Check duplicates")
dup_count = df_fs.groupBy("id_mhs").count().filter("count > 1").count()
print(f"  Duplicate id_mhs: {dup_count}")

# Step 6: Check NULLs
print("\nStep 6: NULL checks")
for col_name in df_fs.columns:
    null_cnt = df_fs.filter(F.col(col_name).isNull()).count()
    print(f"  {col_name}: {null_cnt} NULLs")

# Step 7: Label distribution
print("\nStep 7: Label distribution")
df_fs.groupBy("status_kelulusan").count().orderBy(F.col("count").desc()).show()

# Step 8: Feature statistics
print("\nStep 8: Feature statistics")
df_fs.select(
    F.mean("ipk").alias("mean_ipk"),
    F.min("ipk").alias("min_ipk"),
    F.max("ipk").alias("max_ipk"),
    F.mean("total_sks").alias("mean_total_sks"),
    F.mean("jumlah_mk").alias("mean_jumlah_mk"),
    F.mean("semester").alias("mean_semester")
).show()

# Show schema and sample
print("\nFeature Store schema:")
df_fs.printSchema()

print("\nFeature Store sample (10 rows):")
df_fs.show(10, truncate=False)

# ============================================================
# Write to Iceberg Feature Store
# ============================================================
print("=" * 60)
print("WRITING TO ICEBERG FEATURE STORE")
print("=" * 60)

fs_table = "iceberg.feature_store.feature_store_graduation_prediction"

# Drop existing Feature Store table
spark.sql(f"DROP TABLE IF EXISTS {fs_table}")

# Write as Iceberg table
(
    df_fs.writeTo(fs_table)
    .using("iceberg")
    .createOrReplace()
)

print(f"Table {fs_table} created successfully")

# ============================================================
# Final validation via Spark SQL
# ============================================================
print("=" * 60)
print("FINAL VALIDATION VIA SPARK SQL")
print("=" * 60)

df_validate = spark.table(fs_table)
print(f"Feature Store row count: {df_validate.count()}")
print(f"Feature Store columns: {df_validate.columns}")
df_validate.printSchema()

# Show sample
df_validate.show(10, truncate=False)

# Table location
print("Table location:")
location = spark.sql(f"SHOW CREATE TABLE {fs_table}").collect()
for row in location:
    print(f"  {row[0]}")

spark.stop()
print("=" * 60)
print("FEATURE_STORE_CREATION_COMPLETE")
print("=" * 60)
