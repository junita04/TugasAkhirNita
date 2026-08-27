"""
Create Silver layer from Bronze.
- Trims whitespace on all string columns
- Converts empty strings to NULL
- Converts string 'NaN'/'nan' to NULL
- Removes duplicate rows
- For data_referensi_mahasiswa: removes NULL tanggal_masuk, standardizes jenis_kelamin to uppercase
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
    .appName("TA_Silver_Clean_Data_Referensi_Mahasiswa")
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
# Read Bronze
# ============================================================
print("=" * 60)
print("READING BRONZE TABLE")
print("=" * 60)

bronze_table = "iceberg.bronze.data_referensi_mahasiswa"
df_bronze = spark.table(bronze_table)

bronze_count = df_bronze.count()
bronze_columns = df_bronze.columns
print(f"Bronze table: {bronze_table}")
print(f"Bronze row count: {bronze_count}")
print(f"Bronze columns: {bronze_columns}")
df_bronze.printSchema()

# ============================================================
# AUDIT BEFORE CLEANING
# ============================================================
print("=" * 60)
print("AUDIT BEFORE CLEANING")
print("=" * 60)

# NULL checks before cleaning
null_tanggal_masuk_before = df_bronze.filter(F.col("tanggal_masuk").isNull()).count()
null_tanggal_keluar_before = df_bronze.filter(F.col("tanggal_keluar").isNull()).count()
print(f"NULL tanggal_masuk BEFORE: {null_tanggal_masuk_before}")
print(f"NULL tanggal_keluar BEFORE: {null_tanggal_keluar_before}")

# String "NaN" checks before cleaning
nan_checks_before = {}
for col_name in bronze_columns:
    cnt = df_bronze.filter(
        F.lower(F.trim(F.col(col_name))) == "nan"
    ).count()
    nan_checks_before[col_name] = cnt
    if cnt > 0:
        print(f"String 'NaN' in '{col_name}' BEFORE: {cnt}")

# Empty string checks before cleaning
empty_checks_before = {}
for col_name in bronze_columns:
    cnt = df_bronze.filter(F.col(col_name).isin("", " ")).count()
    empty_checks_before[col_name] = cnt
    if cnt > 0:
        print(f"Empty string in '{col_name}' BEFORE: {cnt}")

# ============================================================
# Silver Cleaning Step 1: Trim whitespace on all string columns
# ============================================================
print("=" * 60)
print("SILVER CLEANING STEP 1: TRIM WHITESPACE")
print("=" * 60)

df_silver = df_bronze
for col_name in bronze_columns:
    df_silver = df_silver.withColumn(col_name, F.trim(F.col(col_name)))

print("Trim complete")

# ============================================================
# Silver Cleaning Step 2: Convert empty strings to NULL
# ============================================================
print("=" * 60)
print("SILVER CLEANING STEP 2: EMPTY STRING -> NULL")
print("=" * 60)

for col_name in bronze_columns:
    df_silver = df_silver.withColumn(
        col_name,
        F.when(F.col(col_name).isin("", " "), F.lit(None).cast("string"))
         .otherwise(F.col(col_name))
    )

print("Empty string conversion complete")

# ============================================================
# Silver Cleaning Step 2b: Convert string 'NaN'/'nan' to NULL
# ============================================================
print("=" * 60)
print("SILVER CLEANING STEP 2b: STRING 'NaN' -> NULL")
print("=" * 60)

for col_name in bronze_columns:
    df_silver = df_silver.withColumn(
        col_name,
        F.when(F.lower(F.trim(F.col(col_name))).isin("nan", "null", "none", "-"), F.lit(None).cast("string"))
         .otherwise(F.col(col_name))
    )

print("String 'NaN' conversion complete")

# ============================================================
# Silver Cleaning Step 3: Remove duplicates (keep first)
# ============================================================
print("=" * 60)
print("SILVER CLEANING STEP 3: REMOVE DUPLICATES")
print("=" * 60)

before_dedup = df_silver.count()
df_silver = df_silver.dropDuplicates()
after_dedup = df_silver.count()
duplicates_removed = before_dedup - after_dedup
print(f"Duplicates removed: {duplicates_removed}")

# ============================================================
# Silver Cleaning Step 4: Remove NULL tanggal_masuk
# ============================================================
print("=" * 60)
print("SILVER CLEANING STEP 4: REMOVE NULL TANGGAL MASUK")
print("=" * 60)

null_tanggal_masuk_step4 = df_silver.filter(F.col("tanggal_masuk").isNull()).count()
print(f"NULL tanggal_masuk before removal: {null_tanggal_masuk_step4}")

df_silver = df_silver.filter(F.col("tanggal_masuk").isNotNull())

after_filter = df_silver.count()
print(f"Rows after removal: {after_filter}")
print(f"Rows removed: {before_dedup - after_filter}")

# ============================================================
# Silver Cleaning Step 5: Standardize jenis_kelamin to uppercase
# ============================================================
print("=" * 60)
print("SILVER CLEANING STEP 5: STANDARDIZE JENIS KELAMIN")
print("=" * 60)

df_silver = df_silver.withColumn(
    "jenis_kelamin",
    F.upper(F.col("jenis_kelamin"))
)

# Show unique values
print("Unique jenis_kelamin values after standardization:")
df_silver.select("jenis_kelamin").distinct().show()

silver_count = df_silver.count()
print(f"Silver row count after cleaning: {silver_count}")

# ============================================================
# Write to Iceberg Silver
# ============================================================
print("=" * 60)
print("WRITING TO ICEBERG SILVER")
print("=" * 60)

silver_table = "iceberg.silver.data_referensi_mahasiswa"

# Drop existing Silver table (old data)
spark.sql(f"DROP TABLE IF EXISTS {silver_table}")

# Write as Iceberg table
(
    df_silver.writeTo(silver_table)
    .using("iceberg")
    .createOrReplace()
)

print(f"Table {silver_table} created successfully")

# ============================================================
# AUDIT AFTER CLEANING
# ============================================================
print("=" * 60)
print("AUDIT AFTER CLEANING")
print("=" * 60)

df_validate = spark.table(silver_table)
validate_count = df_validate.count()
print(f"Silver row count: {validate_count}")
print(f"Silver columns: {df_validate.columns}")
df_validate.printSchema()

# NULL checks
null_tanggal_masuk_after = df_validate.filter(F.col("tanggal_masuk").isNull()).count()
print(f"NULL tanggal_masuk AFTER: {null_tanggal_masuk_after}")

# String "NaN" checks after cleaning
print("String 'NaN' check on ALL columns after cleaning:")
for col_name in df_validate.columns:
    nan_cnt = df_validate.filter(
        F.lower(F.trim(F.col(col_name))) == "nan"
    ).count()
    if nan_cnt > 0:
        print(f"  WARNING: {col_name} has {nan_cnt} 'NaN' strings")
    else:
        print(f"  {col_name}: 0 'NaN' strings")

# Duplicate check
dup_count = df_validate.groupBy("id_mhs").count().filter("count > 1").count()
print(f"Duplicate id_mhs: {dup_count}")

# Empty string checks
print("Empty string check on ALL columns:")
for col_name in df_validate.columns:
    empty_cnt = df_validate.filter(F.col(col_name).isin("", " ")).count()
    if empty_cnt > 0:
        print(f"  WARNING: {col_name} has {empty_cnt} empty strings")

# Jenis kelamin uppercase check
not_uppercase = df_validate.filter(
    F.col("jenis_kelamin") != F.upper(F.col("jenis_kelamin"))
).count()
print(f"jenis_kelamin not uppercase: {not_uppercase}")

# Status mahasiswa distribution
print("Status mahasiswa distribution:")
df_validate.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).show()

# Show sample
print("Sample data (10 rows):")
df_validate.show(10, truncate=False)

# Table location
print("Table location:")
location = spark.sql("SHOW CREATE TABLE iceberg.silver.data_referensi_mahasiswa").collect()
for row in location:
    print(f"  {row[0]}")

# ============================================================
# Summary
# ============================================================
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Bronze rows: {bronze_count}")
print(f"Silver rows: {validate_count}")
print(f"Rows removed: {bronze_count - validate_count}")
print(f"Duplicates removed: {duplicates_removed}")
print(f"NULL tanggal_masuk removed: {null_tanggal_masuk_step4}")
print(f"Silver table: {silver_table}")

spark.stop()
print("=" * 60)
print("CREATE_SILVER_COMPLETE")
print("=" * 60)
