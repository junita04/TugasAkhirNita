"""Show Feature Store datasets"""
import warnings
warnings.filterwarnings("ignore")
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

spark = (
    SparkSession.builder
    .appName("TA_Show_FS")
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

TARGET_IDS = ["MHS000063", "MHS000361", "MHS024954"]

# ============================================================
# 1. TRAINING KELULUSAN
# ============================================================
print("=" * 70)
print("FEATURE STORE: training_kelulusan")
print("=" * 70)

df_train = spark.table("iceberg.feature_store.training_kelulusan")
print(f"Rows: {df_train.count()}")
print(f"Columns: {df_train.columns}")
df_train.printSchema()

print("\nLabel distribution:")
for row in df_train.groupBy("label").count().orderBy(F.col("count").desc()).collect():
    print(f"  {row.label}: {row['count']}")

print("\nSample (20 rows):")
df_train.show(20, truncate=False)

print("\n--- 3 Target IDs ---")
for mid in TARGET_IDS:
    rows = df_train.filter(F.col("id_mhs") == mid).collect()
    if rows:
        r = rows[0]
        print(f"  {mid}: angkatan={r.angkatan}, jk={r.jenis_kelamin}, ipk={r.ipk}, sks={r.total_sks}, mk={r.jumlah_mk}, label={r.label}")
    else:
        print(f"  {mid}: TIDAK ADA (bukan Lulus)")

# ============================================================
# 2. INFERENCE MAHASISWA AKTIF
# ============================================================
print("\n" + "=" * 70)
print("FEATURE STORE: inference_mahasiswa_aktif")
print("=" * 70)

df_inf = spark.table("iceberg.feature_store.inference_mahasiswa_aktif")
print(f"Rows: {df_inf.count()}")
print(f"Columns: {df_inf.columns}")
df_inf.printSchema()

print("\nSample (20 rows):")
df_inf.show(20, truncate=False)

print("\n--- 3 Target IDs ---")
for mid in TARGET_IDS:
    rows = df_inf.filter(F.col("id_mhs") == mid).collect()
    if rows:
        r = rows[0]
        print(f"  {mid}: angkatan={r.angkatan}, jk={r.jenis_kelamin}, ipk={r.ipk}, sks={r.total_sks}, mk={r.jumlah_mk}, target_sks={r.target_sks_kumulatif}, selisih={r.selisih_sks}")
    else:
        print(f"  {mid}: TIDAK DITEMUKAN")

# ============================================================
# 3. OLD FEATURE STORE (comparison)
# ============================================================
print("\n" + "=" * 70)
print("FEATURE STORE LAMA: feature_store_graduation_prediction")
print("=" * 70)

try:
    df_old = spark.table("iceberg.feature_store.feature_store_graduation_prediction")
    print(f"Rows: {df_old.count()}")
    print(f"Columns: {df_old.columns}")
    df_old.printSchema()

    print("\nLabel distribution:")
    for row in df_old.groupBy("status_kelulusan").count().orderBy(F.col("count").desc()).collect():
        print(f"  {row.status_kelulusan}: {row['count']}")

    print("\nSample (10 rows):")
    df_old.show(10, truncate=False)
except Exception as e:
    print(f"Error: {e}")

spark.stop()
