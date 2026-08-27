"""Show sample data from Training and Inference Feature Store"""
import warnings
warnings.filterwarnings("ignore")
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

spark = (
    SparkSession.builder
    .appName("TA_Show_FS_Samples")
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
# TRAINING DATA
# ============================================================
df_train = spark.table("iceberg.feature_store.training_kelulusan")

print("=" * 70)
print("DATA TRAINING (training_kelulusan)")
print("=" * 70)
print(f"Total rows: {df_train.count()}")
print(f"Columns: {df_train.columns}")

print("\n--- Contoh TEPAT WAKTU (10 baris) ---")
df_train.filter(F.col("label") == "Tepat Waktu").show(10, truncate=False)

print("\n--- Contoh TERLAMBAT (10 baris) ---")
df_train.filter(F.col("label") == "Terlambat").show(10, truncate=False)

# ============================================================
# INFERENCE DATA
# ============================================================
df_inf = spark.table("iceberg.feature_store.inference_mahasiswa_aktif")

print("=" * 70)
print("DATA INFERENSI (inference_mahasiswa_aktif)")
print("=" * 70)
print(f"Total rows: {df_inf.count()}")
print(f"Columns: {df_inf.columns}")

print("\n--- Sample 20 baris ---")
df_inf.show(20, truncate=False)

# 3 Target IDs
print("\n--- 3 MAHASISWA AUDIT ---")
for mid in TARGET_IDS:
    rows = df_inf.filter(F.col("id_mhs") == mid).collect()
    if rows:
        r = rows[0]
        print(f"  {mid}: jk={r.jenis_kelamin}, angkatan={r.angkatan}, ipk={r.ipk}, sks={r.total_sks}, mk={r.jumlah_mk}, target_sks={r.target_sks_kumulatif}, selisih={r.selisih_sks}")

# Show as pandas for cleaner view
print("\n" + "=" * 70)
print("TRAINING DATA (pandas view — 10 baris pertama)")
print("=" * 70)
pdf_train = df_train.toPandas()
print(pdf_train.head(10).to_string(index=False))

print("\n" + "=" * 70)
print("INFERENCE DATA (pandas view — 10 baris pertama)")
print("=" * 70)
pdf_inf = df_inf.toPandas()
print(pdf_inf.head(10).to_string(index=False))

# 3 Target IDs in inference
print("\n" + "=" * 70)
print("3 MAHASISWA AUDIT (inference)")
print("=" * 70)
pdf_3 = pdf_inf[pdf_inf["id_mhs"].isin(TARGET_IDS)]
print(pdf_3.to_string(index=False))

spark.stop()
