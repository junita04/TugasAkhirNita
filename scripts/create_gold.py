"""
Create Gold layer from Silver.
Feature Engineering for graduation prediction.

Features:
1. Angkatan - year from tanggal_masuk
2. Semester - based on Angkatan with snapshot year 2026
3. Target SKS Kumulatif - based on curriculum
4. Selisih SKS - Total SKS Aktual - Target SKS Kumulatif
5. Lama Studi - Tanggal Keluar - Tanggal Masuk (in years)
6. Status Kelulusan - Tepat Waktu / Terlambat
"""
import sys
import os

sys.path.insert(0, "/opt/airflow")

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

# ============================================================
# Initialize Spark with Iceberg
# ============================================================
print("=" * 60)
print("INITIALIZING SPARK WITH ICEBERG")
print("=" * 60)

spark = (
    SparkSession.builder
    .appName("TA_Gold_Feature_Engineering")
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
# Read Silver
# ============================================================
print("=" * 60)
print("READING SILVER TABLE")
print("=" * 60)

silver_table = "iceberg.silver.data_referensi_mahasiswa"
df_silver = spark.table(silver_table)

silver_count = df_silver.count()
silver_columns = df_silver.columns
print(f"Silver table: {silver_table}")
print(f"Silver row count: {silver_count}")
print(f"Silver columns: {silver_columns}")
df_silver.printSchema()

# Show sample
df_silver.show(5, truncate=False)

# ============================================================
# Feature Engineering
# ============================================================
print("=" * 60)
print("FEATURE ENGINEERING")
print("=" * 60)

# Cast columns to proper types
df_gold = df_silver.withColumn("total_sks", F.col("total_sks").cast("int"))
df_gold = df_gold.withColumn("jumlah_mk", F.col("jumlah_mk").cast("int"))
df_gold = df_gold.withColumn("ipk", F.col("ipk").cast("double"))
df_gold = df_gold.withColumn("tanggal_masuk", F.to_date(F.col("tanggal_masuk"), "yyyy-MM-dd"))
df_gold = df_gold.withColumn("tanggal_keluar", F.to_date(F.col("tanggal_keluar"), "yyyy-MM-dd"))

# 1. Angkatan (year from tanggal_masuk)
df_gold = df_gold.withColumn("angkatan", F.year(F.col("tanggal_masuk")))
print("1. Angkatan created")

# 2. Semester (based on Angkatan with snapshot year 2026)
# User specification:
# Angkatan 2026 -> Semester 1, 2025 -> 3, 2024 -> 5, 2023 -> 7, 2022 -> 9
# For older angkatan (<=2021), they are graduated, semester = 9
df_gold = df_gold.withColumn(
    "semester",
    F.when(F.col("angkatan") == 2026, F.lit(1))
     .when(F.col("angkatan") == 2025, F.lit(3))
     .when(F.col("angkatan") == 2024, F.lit(5))
     .when(F.col("angkatan") == 2023, F.lit(7))
     .when(F.col("angkatan") <= 2022, F.lit(9))
     .otherwise(F.lit(None).cast("int"))
)
print("2. Semester created")

# 3. Target SKS Kumulatif (based on Semester)
# Semester 1=17, 2=36, 3=55, 4=75, 5=95, 6=115, 7=135, 8=144
# Semester 9 = graduated = 144 SKS
sks_targets = {
    1: 17, 2: 36, 3: 55, 4: 75,
    5: 95, 6: 115, 7: 135, 8: 144, 9: 144
}

target_sks_expr = F.lit(None).cast("int")
for sem, target in sks_targets.items():
    target_sks_expr = F.when(F.col("semester") == sem, F.lit(target)).otherwise(target_sks_expr)

df_gold = df_gold.withColumn("target_sks_kumulatif", target_sks_expr)
print("3. Target SKS Kumulatif created")

# 4. Selisih SKS (Total SKS Aktual - Target SKS Kumulatif)
df_gold = df_gold.withColumn(
    "selisih_sks",
    F.when(F.col("target_sks_kumulatif").isNotNull(),
           F.col("total_sks") - F.col("target_sks_kumulatif"))
     .otherwise(F.lit(None).cast("int"))
)
print("4. Selisih SKS created")

# 5. Lama Studi (Tanggal Keluar - Tanggal Masuk in years)
df_gold = df_gold.withColumn(
    "lama_studi",
    F.when(F.col("tanggal_keluar").isNotNull(),
           F.round(F.datediff(F.col("tanggal_keluar"), F.col("tanggal_masuk")) / 365.25, 2))
     .otherwise(F.lit(None).cast("double"))
)
print("5. Lama Studi created")

# 6. Status Kelulusan (Tepat Waktu / Terlambat)
# Only for Lulus students: 144 SKS + Lama Studi <= 4 tahun -> Tepat Waktu
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
print("6. Status Kelulusan created")

# Show schema and sample
print("\nGold schema:")
df_gold.printSchema()

print("\nGold sample (10 rows):")
df_gold.show(10, truncate=False)

# ============================================================
# Validation
# ============================================================
print("=" * 60)
print("VALIDATION")
print("=" * 60)

# 1. Row count
gold_count = df_gold.count()
print(f"1. Gold row count: {gold_count}")

# 2. Feature distribution
print("\n2. Angkatan distribution:")
df_gold.groupBy("angkatan").count().orderBy("angkatan").show()

print("3. Semester distribution:")
df_gold.groupBy("semester").count().orderBy("semester").show()

print("4. Status Kelulusan distribution:")
df_gold.groupBy("status_kelulusan").count().orderBy(F.col("count").desc()).show()

# 5. Lama Studi stats for Lulus
print("5. Lama Studi stats for Lulus students:")
df_gold.filter(F.col("status_mahasiswa") == "Lulus").select(
    F.mean("lama_studi").alias("mean_lama_studi"),
    F.min("lama_studi").alias("min_lama_studi"),
    F.max("lama_studi").alias("max_lama_studi")
).show()

# 6. Target SKS Kumulatif distribution
print("6. Target SKS Kumulatif distribution:")
df_gold.groupBy("target_sks_kumulatif").count().orderBy("target_sks_kumulatif").show()

# 7. Selisih SKS stats
print("7. Selisih SKS stats:")
df_gold.select(
    F.mean("selisih_sks").alias("mean_selisih"),
    F.min("selisih_sks").alias("min_selisih"),
    F.max("selisih_sks").alias("max_selisih")
).show()

# 8. NULL checks
print("8. NULL checks:")
for col_name in ["angkatan", "semester", "target_sks_kumulatif", "selisih_sks", "lama_studi", "status_kelulusan"]:
    null_cnt = df_gold.filter(F.col(col_name).isNull()).count()
    print(f"   {col_name}: {null_cnt} NULLs")

# ============================================================
# Write to Iceberg Gold
# ============================================================
print("=" * 60)
print("WRITING TO ICEBERG GOLD")
print("=" * 60)

gold_table = "iceberg.gold.data_referensi_mahasiswa"

# Drop existing Gold table
spark.sql(f"DROP TABLE IF EXISTS {gold_table}")

# Write as Iceberg table
(
    df_gold.writeTo(gold_table)
    .using("iceberg")
    .createOrReplace()
)

print(f"Table {gold_table} created successfully")

# ============================================================
# Final validation via Spark SQL
# ============================================================
print("=" * 60)
print("FINAL VALIDATION VIA SPARK SQL")
print("=" * 60)

df_validate = spark.table(gold_table)
print(f"Gold row count: {df_validate.count()}")
print(f"Gold columns: {df_validate.columns}")
df_validate.printSchema()

# Show sample
df_validate.show(10, truncate=False)

# Table location
print("Table location:")
location = spark.sql(f"SHOW CREATE TABLE {gold_table}").collect()
for row in location:
    print(f"  {row[0]}")

spark.stop()
print("=" * 60)
print("CREATE_GOLD_COMPLETE")
print("=" * 60)
