"""STEP 2-4: Audit Bronze, Silver, Gold — Compare with Source"""
import warnings
warnings.filterwarnings("ignore")
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

TARGET_IDS = ["MHS000063", "MHS000361", "MHS024954"]

spark = (
    SparkSession.builder
    .appName("TA_Audit_Layers")
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
# READ LAYERS
# ============================================================
df_bronze = spark.table("iceberg.bronze.data_referensi_mahasiswa")
df_silver = spark.table("iceberg.silver.data_referensi_mahasiswa")
df_gold = spark.table("iceberg.gold.data_referensi_mahasiswa")

# ============================================================
# STEP 2: AUDIT BRONZE
# ============================================================
print("=" * 70)
print("STEP 2: AUDIT BRONZE")
print("=" * 70)

bronze_count = df_bronze.count()
print(f"Bronze rows: {bronze_count}")
print(f"Bronze columns: {df_bronze.columns}")

print("\nStatus distribution:")
for row in df_bronze.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).collect():
    print(f"  {row.status_mahasiswa}: {row['count']}")

null_tgl = df_bronze.filter(F.col("tanggal_keluar").isNull()).count()
print(f"\nNULL tanggal_keluar: {null_tgl}")

# Angkatan 2023
bronze_2023 = df_bronze.filter(F.year(F.col("tanggal_masuk")) == 2023)
print(f"\nAngkatan 2023: {bronze_2023.count()}")
for row in bronze_2023.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).collect():
    print(f"  {row.status_mahasiswa}: {row['count']}")

# 3 target IDs
print(f"\n--- 3 Target IDs in Bronze ---")
for mid in TARGET_IDS:
    row = df_bronze.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        print(f"  {mid}: status={r.status_mahasiswa}, tgl_masuk={r.tanggal_masuk}, tgl_keluar={r.tanggal_keluar}, ipk={r.ipk}, sks={r.total_sks}, mk={r.jumlah_mk}, jk={r.jenis_kelamin}")
    else:
        print(f"  {mid}: NOT FOUND!")

# ============================================================
# STEP 3: AUDIT SILVER
# ============================================================
print("\n" + "=" * 70)
print("STEP 3: AUDIT SILVER")
print("=" * 70)

silver_count = df_silver.count()
print(f"Silver rows: {silver_count}")
print(f"Silver columns: {df_silver.columns}")

print("\nStatus distribution:")
for row in df_silver.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).collect():
    print(f"  {row.status_mahasiswa}: {row['count']}")

null_tgl_s = df_silver.filter(F.col("tanggal_keluar").isNull()).count()
print(f"\nNULL tanggal_keluar: {null_tgl_s}")

# 3 target IDs
print(f"\n--- 3 Target IDs in Silver ---")
for mid in TARGET_IDS:
    row = df_silver.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        print(f"  {mid}: status={r.status_mahasiswa}, tgl_masuk={r.tanggal_masuk}, tgl_keluar={r.tanggal_keluar}")
    else:
        print(f"  {mid}: NOT FOUND!")

# ============================================================
# STEP 4: AUDIT GOLD
# ============================================================
print("\n" + "=" * 70)
print("STEP 4: AUDIT GOLD")
print("=" * 70)

gold_count = df_gold.count()
print(f"Gold rows: {gold_count}")
print(f"Gold columns: {df_gold.columns}")

print("\nStatus distribution:")
for row in df_gold.groupBy("status_mahasiswa").count().orderBy(F.col("count").desc()).collect():
    print(f"  {row.status_mahasiswa}: {row['count']}")

print("\nStatus kelulusan distribution:")
for row in df_gold.groupBy("status_kelulusan").count().orderBy(F.col("count").desc()).collect():
    print(f"  {row.status_kelulusan}: {row['count']}")

null_tgl_g = df_gold.filter(F.col("tanggal_keluar").isNull()).count()
print(f"\nNULL tanggal_keluar: {null_tgl_g}")

# 3 target IDs — CRITICAL
print(f"\n--- 3 Target IDs in Gold ---")
for mid in TARGET_IDS:
    row = df_gold.filter(F.col("id_mhs") == mid).collect()
    if row:
        r = row[0]
        print(f"  {mid}: status={r.status_mahasiswa}, tgl_keluar={r.tanggal_keluar}, lama_studi={r.lama_studi}, label={r.status_kelulusan}")
        if str(r.status_mahasiswa) != "AKTIF":
            print(f"    *** ANOMALY: Status bukan AKTIF! ***")
        if r.tanggal_keluar is not None:
            print(f"    *** ANOMALY: tanggal_keluar tidak NULL! ***")
    else:
        print(f"  {mid}: NOT FOUND!")

# ============================================================
# LINEAGE COMPARISON
# ============================================================
print("\n" + "=" * 70)
print("LINEAGE COMPARISON — 3 TARGET IDs")
print("=" * 70)

print(f"{'ID':<12} {'Source':>10} {'Bronze':>10} {'Silver':>10} {'Gold':>10}")
print("-" * 55)

for mid in TARGET_IDS:
    src_status = "?"
    brz_status = df_bronze.filter(F.col("id_mhs") == mid).select("status_mahasiswa").collect()
    slv_status = df_silver.filter(F.col("id_mhs") == mid).select("status_mahasiswa").collect()
    gld_row = df_gold.filter(F.col("id_mhs") == mid).collect()
    
    brz = brz_status[0][0] if brz_status else "N/A"
    slv = slv_status[0][0] if slv_status else "N/A"
    gld = gld_row[0].status_mahasiswa if gld_row else "N/A"
    
    print(f"{mid:<12} {'AKTIF':>10} {str(brz):>10} {str(slv):>10} {str(gld):>10}")

print(f"\n{'='*70}")
print("TANGGAL KELUAR LINEAGE")
print(f"{'='*70}")
print(f"{'ID':<12} {'Source':>10} {'Bronze':>10} {'Silver':>10} {'Gold':>10}")
print("-" * 55)

for mid in TARGET_IDS:
    brz = df_bronze.filter(F.col("id_mhs") == mid).select("tanggal_keluar").collect()
    slv = df_silver.filter(F.col("id_mhs") == mid).select("tanggal_keluar").collect()
    gld = df_gold.filter(F.col("id_mhs") == mid).select("tanggal_keluar").collect()
    
    b = brz[0][0] if brz else "N/A"
    s = slv[0][0] if slv else "N/A"
    g = gld[0][0] if gld else "N/A"
    
    print(f"{mid:<12} {str('NULL'):>10} {str(b):>10} {str(s):>10} {str(g):>10}")

spark.stop()
print("\nAUDIT LAYERS COMPLETE")
