"""
END-TO-END DATA LINEAGE AUDIT
Bronze → Silver → Gold → Feature Store

Queries ALL Iceberg tables via PySpark for actual counts.
"""
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import time

# ============================================================
# SPARK SESSION
# ============================================================
spark = (SparkSession.builder
    .appName("EndToEndDataLineageAudit")
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.iceberg.type", "hadoop")
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://warehouse/iceberg")
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin-password")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config("spark.jars", "/opt/airflow/jars/iceberg-spark-runtime-3.5_2.12-1.5.2.jar,/opt/airflow/jars/hadoop-aws-3.3.4.jar,/opt/airflow/jars/aws-java-sdk-bundle-1.12.261.jar")
    .getOrCreate())

spark.sparkContext.setLogLevel("ERROR")

def q(sql):
    """Execute query and return list of Row objects."""
    return spark.sql(sql).collect()

def cnt(table):
    """Return row count."""
    return spark.table(table).count()

def show(sql):
    """Execute and show."""
    spark.sql(sql).show(100, truncate=False)

print("=" * 70)
print("END-TO-END DATA LINEAGE AUDIT")
print("=" * 70)

# ============================================================
# 1. ALL TABLE COUNTS
# ============================================================
print("\n" + "=" * 70)
print("1. ALL TABLE COUNTS")
print("=" * 70)

tables = {
    "Bronze": [
        ("iceberg.bronze.data_referensi_mahasiswa_fix", "1 row = 1 record mahasiswa"),
        ("iceberg.bronze.data_khs_fix", "1 row = 1 record KHS"),
        ("iceberg.bronze.data_program_studi_fix", "1 row = 1 program studi"),
        ("iceberg.bronze.data_kelas_fix", "1 row = 1 kelas"),
        ("iceberg.bronze.data_kurikulum_fix", "1 row = 1 kurikulum"),
    ],
    "Silver": [
        ("iceberg.silver.silver_referensi_mahasiswa_fix", "1 row = 1 mahasiswa (cleaned)"),
        ("iceberg.silver.silver_khs_fix", "1 row = 1 KHS (cleaned)"),
    ],
    "Gold": [
        ("iceberg.gold.dim_mahasiswa_fix", "1 row = 1 mahasiswa"),
        ("iceberg.gold.fact_khs_fix", "1 row = 1 KHS record"),
    ],
    "Feature Store": [
        ("iceberg.feature_store.training_dataset_fix", "1 row = 1 mahasiswa (training)"),
        ("iceberg.feature_store.inference_dataset_fix", "1 row = 1 mahasiswa (inference)"),
    ],
}

counts = {}
for layer, tbl_list in tables.items():
    print(f"\n--- {layer} ---")
    for table, grain in tbl_list:
        c = cnt(table)
        counts[table] = c
        print(f"  {table}: {c} rows  (Grain: {grain})")

# ============================================================
# 2. BRONZE AUDIT
# ============================================================
print("\n" + "=" * 70)
print("2. BRONZE LAYER AUDIT")
print("=" * 70)

# --- Referensi Mahasiswa ---
print("\n--- 2.1 data_referensi_mahasiswa_fix ---")
df = spark.table("iceberg.bronze.data_referensi_mahasiswa_fix")
total_bronze_ref = df.count()
print(f"  Total rows: {total_bronze_ref}")
print(f"  Columns: {len(df.columns)}")
print(f"  Schema:")
for field in df.schema.fields:
    null_cnt = df.filter(F.col(field.name).isNull()).count()
    print(f"    {field.name} ({field.dataType.simpleString()}): {null_cnt} NULLs")

# Check for duplicate mahasiswa
if "id_mahasiswa" in df.columns:
    unique_id = df.select("id_mahasiswa").distinct().count()
    dup = total_bronze_ref - unique_id
    print(f"  Unique id_mahasiswa: {unique_id}")
    print(f"  Duplicate rows (by id_mahasiswa): {dup}")
elif "nim" in df.columns:
    unique_id = df.select("nim").distinct().count()
    dup = total_bronze_ref - unique_id
    print(f"  Unique nim: {unique_id}")
    print(f"  Duplicate rows (by nim): {dup}")

# Show status distribution
if "status_mahasiswa" in df.columns:
    print("  Status distribution:")
    df.groupBy("status_mahasiswa").count().orderBy(F.desc("count")).show(10, truncate=False)

# Show tanggal_masuk NULL count
if "tanggal_masuk" in df.columns:
    null_tgl = df.filter(F.col("tanggal_masuk").isNull()).count()
    print(f"  tanggal_masuk IS NULL: {null_tgl}")
    if null_tgl > 0 and "status_mahasiswa" in df.columns:
        print("  NULL tanggal_masuk by status:")
        df.filter(F.col("tanggal_masuk").isNull()).groupBy("status_mahasiswa").count().orderBy(F.desc("count")).show(10, truncate=False)

# --- KHS ---
print("\n--- 2.2 data_khs_fix ---")
df_khs = spark.table("iceberg.bronze.data_khs_fix")
total_bronze_khs = df_khs.count()
print(f"  Total rows: {total_bronze_khs}")
print(f"  Columns: {len(df_khs.columns)}")
print(f"  Schema:")
for field in df_khs.schema.fields:
    null_cnt = df_khs.filter(F.col(field.name).isNull()).count()
    print(f"    {field.name} ({field.dataType.simpleString()}): {null_cnt} NULLs")

# KHS duplicates
if "id_khs" in df_khs.columns:
    unique_khs = df_khs.select("id_khs").distinct().count()
    print(f"  Unique id_khs: {unique_khs}")
    print(f"  Duplicate rows: {total_bronze_khs - unique_khs}")
elif "id_mahasiswa" in df_khs.columns and "semester" in df_khs.columns:
    unique_khs = df_khs.select("id_mahasiswa", "semester").distinct().count()
    print(f"  Unique (id_mahasiswa, semester): {unique_khs}")
    print(f"  Duplicate rows: {total_bronze_khs - unique_khs}")

# ============================================================
# 3. SILVER AUDIT
# ============================================================
print("\n" + "=" * 70)
print("3. SILVER LAYER AUDIT")
print("=" * 70)

# --- Silver Referensi Mahasiswa ---
print("\n--- 3.1 silver_referensi_mahasiswa_fix ---")
df_silver_ref = spark.table("iceberg.silver.silver_referensi_mahasiswa_fix")
total_silver_ref = df_silver_ref.count()
print(f"  Total rows: {total_silver_ref}")
print(f"  Columns: {len(df_silver_ref.columns)}")

# Check for NULL values
print("  NULL counts:")
for col in df_silver_ref.columns:
    null_cnt = df_silver_ref.filter(F.col(col).isNull()).count()
    if null_cnt > 0:
        print(f"    {col}: {null_cnt}")

# Unique ID
if "id_mahasiswa" in df_silver_ref.columns:
    unique_silver_ref = df_silver_ref.select("id_mahasiswa").distinct().count()
    print(f"  Unique id_mahasiswa: {unique_silver_ref}")
    print(f"  Duplicate rows: {total_silver_ref - unique_silver_ref}")

# Status distribution
if "status_mahasiswa" in df_silver_ref.columns:
    print("  Status distribution:")
    df_silver_ref.groupBy("status_mahasiswa").count().orderBy(F.desc("count")).show(10, truncate=False)

# tanggal_masuk NULL
if "tanggal_masuk" in df_silver_ref.columns:
    null_tgl_silver = df_silver_ref.filter(F.col("tanggal_masuk").isNull()).count()
    print(f"  tanggal_masuk IS NULL: {null_tgl_silver}")
    if null_tgl_silver > 0 and "status_mahasiswa" in df_silver_ref.columns:
        print("  NULL tanggal_masuk by status:")
        df_silver_ref.filter(F.col("tanggal_masuk").isNull()).groupBy("status_mahasiswa").count().orderBy(F.desc("count")).show(10, truncate=False)

# --- Silver KHS ---
print("\n--- 3.2 silver_khs_fix ---")
df_silver_khs = spark.table("iceberg.silver.silver_khs_fix")
total_silver_khs = df_silver_khs.count()
print(f"  Total rows: {total_silver_khs}")
print(f"  Columns: {len(df_silver_khs.columns)}")

# Check for NULL values
print("  NULL counts:")
for col in df_silver_khs.columns:
    null_cnt = df_silver_khs.filter(F.col(col).isNull()).count()
    if null_cnt > 0:
        print(f"    {col}: {null_cnt}")

# Unique keys
if "id_khs" in df_silver_khs.columns:
    unique_silver_khs = df_silver_khs.select("id_khs").distinct().count()
    print(f"  Unique id_khs: {unique_silver_khs}")
    print(f"  Duplicate rows: {total_silver_khs - unique_silver_khs}")

# Check IP = 0
if "ip" in df_silver_khs.columns:
    ip_zero = df_silver_khs.filter(F.col("ip") == 0).count()
    ip_null = df_silver_khs.filter(F.col("ip").isNull()).count()
    print(f"  IP = 0: {ip_zero}")
    print(f"  IP IS NULL: {ip_null}")

# ============================================================
# 4. GOLD AUDIT
# ============================================================
print("\n" + "=" * 70)
print("4. GOLD LAYER AUDIT")
print("=" * 70)

# --- dim_mahasiswa ---
print("\n--- 4.1 dim_mahasiswa_fix ---")
df_gold_mhs = spark.table("iceberg.gold.dim_mahasiswa_fix")
total_gold_mhs = df_gold_mhs.count()
print(f"  Total rows: {total_gold_mhs}")
print(f"  Columns: {len(df_gold_mhs.columns)}")

# Unique ID
if "id_mahasiswa" in df_gold_mhs.columns:
    unique_gold_mhs = df_gold_mhs.select("id_mahasiswa").distinct().count()
    print(f"  Unique id_mahasiswa: {unique_gold_mhs}")
    print(f"  Duplicate rows: {total_gold_mhs - unique_gold_mhs}")

# Status distribution
if "status_mahasiswa" in df_gold_mhs.columns:
    print("  Status distribution:")
    df_gold_mhs.groupBy("status_mahasiswa").count().orderBy(F.desc("count")).show(10, truncate=False)

# Angkatan distribution
if "angkatan" in df_gold_mhs.columns:
    print("  Angkatan distribution:")
    df_gold_mhs.groupBy("angkatan").count().orderBy("angkatan").show(20, truncate=False)

# --- fact_khs ---
print("\n--- 4.2 fact_khs_fix ---")
df_gold_khs = spark.table("iceberg.gold.fact_khs_fix")
total_gold_khs = df_gold_khs.count()
print(f"  Total rows: {total_gold_khs}")
print(f"  Columns: {len(df_gold_khs.columns)}")

# Unique keys
if "id_mahasiswa" in df_gold_khs.columns:
    unique_gold_khs = df_gold_khs.select("id_mahasiswa").distinct().count()
    print(f"  Unique id_mahasiswa: {unique_gold_khs}")
    print(f"  Duplicate rows (by id_mahasiswa): {total_gold_khs - unique_gold_khs}")

# IP = 0 check
if "ip" in df_gold_khs.columns:
    ip_zero_gold = df_gold_khs.filter(F.col("ip") == 0).count()
    ip_null_gold = df_gold_khs.filter(F.col("ip").isNull()).count()
    print(f"  IP = 0: {ip_zero_gold}")
    print(f"  IP IS NULL: {ip_null_gold}")

# Check mahasiswa with/without KHS
if "id_mahasiswa" in df_gold_mhs.columns and "id_mahasiswa" in df_gold_khs.columns:
    mhs_ids = df_gold_mhs.select("id_mahasiswa").distinct()
    khs_ids = df_gold_khs.select("id_mahasiswa").distinct()
    mhs_with_khs = mhs_ids.join(khs_ids, "id_mahasiswa", "inner").count()
    mhs_without_khs = mhs_ids.join(khs_ids, "id_mahasiswa", "left_anti").count()
    print(f"\n  Mahasiswa with KHS: {mhs_with_khs}")
    print(f"  Mahasiswa without KHS: {mhs_without_khs}")

# SKS stats
if "selisih_sks" in df_gold_khs.columns:
    print("\n  selisih_sks statistics:")
    df_gold_khs.select(
        F.min("selisih_sks").alias("min"),
        F.max("selisih_sks").alias("max"),
        F.avg("selisih_sks").alias("avg"),
        F.sum(F.when(F.col("selisih_sks").isNull(), 1).otherwise(0)).alias("null_count"),
        F.sum(F.when(F.col("selisih_sks") < 0, 1).otherwise(0)).alias("negative_count"),
        F.sum(F.when(F.col("selisih_sks") == 0, 1).otherwise(0)).alias("zero_count"),
        F.sum(F.when(F.col("selisih_sks") > 0, 1).otherwise(0)).alias("positive_count"),
    ).show(10, truncate=False)

# Label distribution
if "label" in df_gold_mhs.columns:
    print("\n  Label distribution:")
    df_gold_mhs.groupBy("label").count().orderBy("label").show(10, truncate=False)

# ============================================================
# 5. FEATURE STORE AUDIT
# ============================================================
print("\n" + "=" * 70)
print("5. FEATURE STORE AUDIT")
print("=" * 70)

# --- Training ---
print("\n--- 5.1 training_dataset_fix ---")
df_train = spark.table("iceberg.feature_store.training_dataset_fix")
total_train = df_train.count()
print(f"  Total rows: {total_train}")
print(f"  Columns: {len(df_train.columns)}")
print(f"  Column names: {df_train.columns}")

# Label distribution
if "label" in df_train.columns:
    print("  Label distribution:")
    df_train.groupBy("label").count().orderBy("label").show(10, truncate=False)

# Angkatan distribution
if "angkatan" in df_train.columns:
    print("  Angkatan distribution:")
    df_train.groupBy("angkatan").count().orderBy("angkatan").show(20, truncate=False)

# Status distribution
if "status_mahasiswa" in df_train.columns:
    print("  Status distribution:")
    df_train.groupBy("status_mahasiswa").count().orderBy(F.desc("count")).show(10, truncate=False)

# Check 2022 in training
if "angkatan" in df_train.columns:
    train_2022 = df_train.filter(F.col("angkatan") == 2022).count()
    print(f"  2022 in training: {train_2022}")

# Unique ID
if "id_mahasiswa" in df_train.columns:
    unique_train = df_train.select("id_mahasiswa").distinct().count()
    print(f"  Unique id_mahasiswa: {unique_train}")
    print(f"  Duplicate rows: {total_train - unique_train}")

# --- Inference ---
print("\n--- 5.2 inference_dataset_fix ---")
df_inf = spark.table("iceberg.feature_store.inference_dataset_fix")
total_inf = df_inf.count()
print(f"  Total rows: {total_inf}")
print(f"  Columns: {len(df_inf.columns)}")
print(f"  Column names: {df_inf.columns}")

# Angkatan distribution
if "angkatan" in df_inf.columns:
    print("  Angkatan distribution:")
    df_inf.groupBy("angkatan").count().orderBy("angkatan").show(20, truncate=False)

# Status distribution
if "status_mahasiswa" in df_inf.columns:
    print("  Status distribution:")
    df_inf.groupBy("status_mahasiswa").count().orderBy(F.desc("count")).show(10, truncate=False)

# Unique ID
if "id_mahasiswa" in df_inf.columns:
    unique_inf = df_inf.select("id_mahasiswa").distinct().count()
    print(f"  Unique id_mahasiswa: {unique_inf}")
    print(f"  Duplicate rows: {total_inf - unique_inf}")

# Overlap check
if "id_mahasiswa" in df_train.columns and "id_mahasiswa" in df_inf.columns:
    train_ids = df_train.select("id_mahasiswa").distinct()
    inf_ids = df_inf.select("id_mahasiswa").distinct()
    overlap = train_ids.join(inf_ids, "id_mahasiswa", "inner").count()
    print(f"\n  OVERLAP between training and inference: {overlap}")

# ============================================================
# 6. ANGKATAN RECONCILIATION (Mahasiswa)
# ============================================================
print("\n" + "=" * 70)
print("6. ANGKATAN RECONCILIATION (dim_mahasiswa_fix)")
print("=" * 70)

# Gold angkatan
gold_angkatan = df_gold_mhs.groupBy("angkatan").count().orderBy("angkatan")
print("\nGold dim_mahasiswa_fix by angkatan:")
gold_angkatan.show(20, truncate=False)

# Training angkatan
train_angkatan = df_train.groupBy("angkatan").count().orderBy("angkatan")
print("\nTraining by angkatan:")
train_angkatan.show(20, truncate=False)

# Inference angkatan
inf_angkatan = df_inf.groupBy("angkatan").count().orderBy("angkatan")
print("\nInference by angkatan:")
inf_angkatan.show(20, truncate=False)

# ============================================================
# 7. QUALITY CHECKS
# ============================================================
print("\n" + "=" * 70)
print("7. QUALITY CHECKS")
print("=" * 70)

checks = []

# CHECK 1: No duplicate in Gold
if "id_mahasiswa" in df_gold_mhs.columns:
    dup_gold = total_gold_mhs - unique_gold_mhs
    checks.append(("No duplicate ID in Gold", dup_gold == 0, f"Duplicates: {dup_gold}"))

# CHECK 2: No 2022 in Training
if "angkatan" in df_train.columns:
    checks.append(("No 2022 in Training", train_2022 == 0, f"2022 count: {train_2022}"))

# CHECK 3: 2022 in Inference
if "angkatan" in df_inf.columns:
    inf_2022 = df_inf.filter(F.col("angkatan") == 2022).count()
    checks.append(("2022 in Inference", inf_2022 > 0, f"2022 count: {inf_2022}"))

# CHECK 4: No overlap
if "id_mahasiswa" in df_train.columns and "id_mahasiswa" in df_inf.columns:
    checks.append(("No Training/Inference overlap", overlap == 0, f"Overlap: {overlap}"))

# CHECK 5: IP = 0 preserved
if "ip" in df_gold_khs.columns:
    checks.append(("IP = 0 preserved", ip_zero_gold >= 0, f"IP=0 count: {ip_zero_gold}"))

# CHECK 6: Gold grain = 1 mahasiswa
if "id_mahasiswa" in df_gold_mhs.columns:
    checks.append(("Gold grain = 1 mahasiswa", unique_gold_mhs == total_gold_mhs, f"Unique: {unique_gold_mhs}, Total: {total_gold_mhs}"))

for name, passed, detail in checks:
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}: {detail}")

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)

print(f"""
BRONZE:
  data_referensi_mahasiswa_fix : {counts['iceberg.bronze.data_referensi_mahasiswa_fix']}
  data_khs_fix                 : {counts['iceberg.bronze.data_khs_fix']}

SILVER:
  silver_referensi_mahasiswa_fix : {counts['iceberg.silver.silver_referensi_mahasiswa_fix']}
  silver_khs_fix                 : {counts['iceberg.silver.silver_khs_fix']}

GOLD:
  dim_mahasiswa_fix : {counts['iceberg.gold.dim_mahasiswa_fix']}
  fact_khs_fix      : {counts['iceberg.gold.fact_khs_fix']}

FEATURE STORE:
  training_dataset_fix  : {counts['iceberg.feature_store.training_dataset_fix']}
  inference_dataset_fix : {counts['iceberg.feature_store.inference_dataset_fix']}

QUALITY CHECKS: {sum(1 for _, p, _ in checks if p)}/{len(checks)} PASSED
""")

spark.stop()
print("DONE.")
